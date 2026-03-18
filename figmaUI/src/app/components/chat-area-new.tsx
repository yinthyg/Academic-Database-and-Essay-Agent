import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";
import { useAuth } from "../lib/auth-context";
import * as api from "../lib/api";

interface ChatAreaNewProps {
  conversationId: number | null;
}

export function ChatAreaNew({ conversationId }: ChatAreaNewProps) {
  const { token } = useAuth();
  const [messages, setMessages] = useState<api.Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const streamBufferRef = useRef<string>("");
  const typingTimerRef = useRef<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (conversationId && token) {
      loadMessages();
    } else {
      setMessages([]);
    }
  }, [conversationId, token]);

  useEffect(() => {
    return () => {
      if (typingTimerRef.current != null) {
        window.clearInterval(typingTimerRef.current);
        typingTimerRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingContent]);

  const loadMessages = async () => {
    if (!token || !conversationId) return;

    try {
      const data = await api.getConversationMessages(token, conversationId);
      setMessages(data);
    } catch (error) {
      console.error("Failed to load messages:", error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading || !token || !conversationId) return;

    const userInput = input;
    setInput("");
    setIsLoading(true);
    setStreamingContent("");
    setIsThinking(true);
    streamBufferRef.current = "";

    try {
      // Create user message
      await api.createMessage(token, conversationId, {
        role: "user",
        content: userInput,
      });

      // Stream assistant response
      await api.chatStream(
        token,
        conversationId,
        (chunk) => {
          // First chunk means model has started producing tokens
          if (isThinking) setIsThinking(false);
          streamBufferRef.current += chunk;
          // Typewriter effect: flush buffer char-by-char for a smoother "one char at a time" feel.
          if (typingTimerRef.current == null) {
            typingTimerRef.current = window.setInterval(() => {
              if (!streamBufferRef.current) {
                if (typingTimerRef.current != null) {
                  window.clearInterval(typingTimerRef.current);
                  typingTimerRef.current = null;
                }
                return;
              }
              const nextChar = streamBufferRef.current[0];
              streamBufferRef.current = streamBufferRef.current.slice(1);
              setStreamingContent((prev) => prev + nextChar);
            }, 10);
          }
        },
        () => {
          // On stream end, reload all messages
          setStreamingContent("");
          setIsThinking(false);
          streamBufferRef.current = "";
          if (typingTimerRef.current != null) {
            window.clearInterval(typingTimerRef.current);
            typingTimerRef.current = null;
          }
          loadMessages();
          setIsLoading(false);
        }
      );
    } catch (error) {
      console.error("Failed to send message:", error);
      setIsLoading(false);
      setStreamingContent("");
      setIsThinking(false);
      streamBufferRef.current = "";
      if (typingTimerRef.current != null) {
        window.clearInterval(typingTimerRef.current);
        typingTimerRef.current = null;
      }
    }
  };

  if (!conversationId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Welcome to Research Copilot
          </h2>
          <p className="text-gray-500">
            Select a conversation or create a new one to get started
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 p-4 bg-white">
        <h2 className="text-lg font-semibold text-gray-900">Research Chat</h2>
        <p className="text-sm text-gray-500">Ask questions about research papers</p>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-6" ref={scrollRef}>
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] ${
                  message.role === "user"
                    ? "bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3"
                    : "space-y-3"
                }`}
              >
                {message.role === "user" ? (
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {message.content}
                  </p>
                ) : (
                  <>
                    {/* Tool Source Badge */}
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline" className="text-xs">
                        RAG Search
                      </Badge>
                    </div>

                    {/* Assistant Message Content */}
                    <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
                      <p className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </p>
                    </div>

                    {/* Sources/Citations */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <h4 className="text-xs font-semibold text-blue-900 mb-2">
                          References
                        </h4>
                        <div className="space-y-2">
                          {message.sources.map((source, idx) => (
                            <div
                              key={idx}
                              className="text-xs text-blue-900 flex items-start gap-2"
                            >
                              <span className="font-mono font-medium">
                                [Doc {source.document_id}]
                              </span>
                              <div className="flex-1">
                                <p className="font-medium">{source.original_name}</p>
                                <p className="text-blue-700 mt-0.5">
                                  Chunk {source.chunk_index}
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}

          {/* Streaming Message */}
          {isLoading && streamingContent && (
            <div className="flex justify-start">
              <div className="max-w-[80%] space-y-3">
                <div className="flex items-center gap-2 mb-2">
                  <Badge variant="outline" className="text-xs">
                    RAG Search
                  </Badge>
                </div>
                <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
                  <p className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">
                    {streamingContent}
                    <span className="inline-block w-1 h-4 bg-gray-900 ml-0.5 animate-pulse" />
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Loading Indicator */}
          {isLoading && !streamingContent && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
                <Loader2 className="size-4 animate-spin text-gray-500" />
                <span className="text-sm text-gray-700">{isThinking ? "模型正在思考..." : "准备输出..."}</span>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <div className="max-w-4xl mx-auto flex gap-3">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask a research question..."
            className="flex-1 min-h-[60px] max-h-[200px] resize-none"
            disabled={isLoading}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            size="lg"
            className="px-6"
          >
            <Send className="size-4" />
          </Button>
        </div>
        <p className="text-xs text-gray-400 text-center mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
