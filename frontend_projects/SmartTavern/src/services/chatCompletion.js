// SmartTavern Frontend API Client — Chat Completion Workflow
// 调用后端 workflow.smarttraven/chat_completion 系列接口
// 默认网关：http://localhost:8050/api/workflow

const DEFAULT_BASE = 'http://localhost:8050/api/workflow';

function ensureBase() {
  const fromWindow = typeof window !== 'undefined' && window.ST_API_BASE;
  return String(fromWindow || DEFAULT_BASE).replace(/\/+$/, '');
}

async function postJSON(path, body = {}) {
  const base = ensureBase();
  const url = `${base}/${String(path).replace(/^\/+/, '')}`;
  let resp;
  try {
    resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
  } catch (networkError) {
    const err = new Error(`[ChatCompletion] Network error: ${networkError?.message || networkError}`);
    err.cause = networkError;
    err.url = url;
    throw err;
  }

  let data = null;
  const text = await resp.text().catch(() => '');
  try {
    data = text ? JSON.parse(text) : null;
  } catch (parseError) {
    const err = new Error(`[ChatCompletion] Invalid JSON response (${resp.status}): ${text?.slice(0, 200)}`);
    err.cause = parseError;
    err.status = resp.status;
    err.url = url;
    throw err;
  }

  if (!resp.ok) {
    const err = new Error(`[ChatCompletion] HTTP ${resp.status}: ${data && (data.message || data.error) || 'Unknown error'}`);
    err.status = resp.status;
    err.url = url;
    err.details = data;
    throw err;
  }
  return data;
}

const ChatCompletion = {
  /**
   * 非流式AI补全
   * @param {string} conversationFile - 对话文件路径
   * @param {string} llmConfigFile - LLM配置文件路径
   * @returns {Promise<Object>} { success, node_id, content, usage, response_time, model_used, doc }
   */
  async complete({ conversationFile, llmConfigFile }) {
    if (!conversationFile || !llmConfigFile) {
      throw new Error('[ChatCompletion] conversationFile and llmConfigFile are required');
    }
    
    return postJSON('smarttraven/chat_completion/complete', {
      conversation_file: conversationFile,
      llm_config_file: llmConfigFile
    });
  },

  /**
   * 流式AI补全（使用fetch + ReadableStream）
   * @param {string} conversationFile - 对话文件路径
   * @param {string} llmConfigFile - LLM配置文件路径
   * @param {Object} callbacks - 回调函数
   * @param {Function} callbacks.onChunk - 收到文本块时调用 (content: string)
   * @param {Function} callbacks.onFinish - 完成时调用 (finish_reason: string)
   * @param {Function} callbacks.onUsage - 收到用量信息时调用 (usage: object)
   * @param {Function} callbacks.onSaved - 保存成功时调用 ({ node_id, doc })
   * @param {Function} callbacks.onError - 错误时调用 (message: string)
   * @param {Function} callbacks.onEnd - 流结束时调用 ()
   * @returns {Object} { abort: Function } - 可用于取消请求
   */
  completeStream({ conversationFile, llmConfigFile, callbacks = {} }) {
    if (!conversationFile || !llmConfigFile) {
      throw new Error('[ChatCompletion] conversationFile and llmConfigFile are required');
    }

    const base = ensureBase();
    const url = `${base}/smarttraven/chat_completion/complete_stream`;

    const abortController = new AbortController();

    // 使用 fetch API 进行 POST 请求
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({
        conversation_file: conversationFile,
        llm_config_file: llmConfigFile
      }),
      signal: abortController.signal
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      // 递归读取流
      function readChunk() {
        reader.read().then(({ done, value }) => {
          if (done) {
            return;
          }

          // 解码并添加到缓冲区
          buffer += decoder.decode(value, { stream: true });

          // 按行处理
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // 保留最后不完整的行

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6).trim();
              if (!dataStr) continue;

              try {
                const data = JSON.parse(dataStr);

                switch (data.type) {
                  case 'chunk':
                    callbacks.onChunk?.(data.content);
                    break;
                  case 'finish':
                    callbacks.onFinish?.(data.finish_reason);
                    break;
                  case 'usage':
                    callbacks.onUsage?.(data.usage);
                    break;
                  case 'saved':
                    callbacks.onSaved?.({
                      node_id: data.node_id,
                      doc: data.doc,
                      usage: data.usage
                    });
                    break;
                  case 'error':
                    callbacks.onError?.(data.message);
                    return; // 停止读取
                  case 'end':
                    callbacks.onEnd?.();
                    return; // 停止读取
                }
              } catch (err) {
                console.error('[ChatCompletion] Failed to parse SSE data:', err);
              }
            }
          }

          // 继续读取下一块
          readChunk();
        }).catch(err => {
          if (err.name !== 'AbortError') {
            console.error('[ChatCompletion] Stream read error:', err);
            callbacks.onError?.('Stream read error');
          }
        });
      }

      readChunk();
    })
    .catch(err => {
      if (err.name !== 'AbortError') {
        console.error('[ChatCompletion] Fetch error:', err);
        callbacks.onError?.(err.message || 'Request failed');
      }
    });

    return {
      abort: () => abortController.abort()
    };
  },
};

export default ChatCompletion;