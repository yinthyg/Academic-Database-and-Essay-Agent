import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";
import { StreamingText } from "./streaming-text";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  toolSource?: "RAG Search" | "Paper Compare";
  isStreaming?: boolean;
}

interface Citation {
  paperId: string;
  title: string;
  relevance?: string;
}

const mockMessages: Message[] = [
  {
    id: "msg-1",
    role: "user",
    content: "Can you explain the key innovations in transformer architectures?",
  },
  {
    id: "msg-2",
    role: "assistant",
    content:
      "Transformer architectures introduced several groundbreaking innovations:\n\n1. **Self-Attention Mechanism**: Unlike RNNs, transformers use self-attention to process all tokens in parallel, allowing the model to weigh the importance of different parts of the input sequence.\n\n2. **Positional Encoding**: Since transformers don't have inherent sequential structure, positional encodings are added to give the model information about token positions.\n\n3. **Multi-Head Attention**: This allows the model to attend to information from different representation subspaces at different positions.\n\nThese innovations enabled better parallelization and the ability to capture long-range dependencies more effectively than previous architectures.",
    citations: [
      {
        paperId: "paper:12",
        title: "Attention Is All You Need",
        relevance: "Original transformer paper",
      },
      {
        paperId: "paper:45",
        title: "BERT: Pre-training of Deep Bidirectional Transformers",
        relevance: "Transformer application",
      },
    ],
    toolSource: "RAG Search",
  },
];

interface ChatAreaProps {
  conversationId: string;
}

export function ChatArea({ conversationId }: ChatAreaProps) {
  const [messages, setMessages] = useState<Message[]>(mockMessages);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Simulate streaming response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: `msg-${Date.now()}-ai`,
        role: "assistant",
        content:
          "Based on recent research, I can provide insights into your question. The key findings suggest that this approach has shown promising results across multiple domains...",
        isStreaming: true,
        toolSource: "RAG Search",
        citations: [
          {
            paperId: "paper:78",
            title: "Recent Advances in AI Research",
          },
        ],
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000);
  };

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
                    {message.toolSource && (
                      <div className="flex items-center gap-2 mb-2">
                        <Badge variant="outline" className="text-xs">
                          {message.toolSource}
                        </Badge>
                      </div>
                    )}

                    {/* Assistant Message Content */}
                    <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
                      {message.isStreaming ? (
                        <StreamingText text={message.content} />
                      ) : (
                        <p className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">
                          {message.content}
                        </p>
                      )}
                    </div>

                    {/* Citations */}
                    {message.citations && message.citations.length > 0 && (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <h4 className="text-xs font-semibold text-blue-900 mb-2">
                          References
                        </h4>
                        <div className="space-y-2">
                          {message.citations.map((citation, idx) => (
                            <div
                              key={idx}
                              className="text-xs text-blue-900 flex items-start gap-2"
                            >
                              <span className="font-mono font-medium">
                                [{citation.paperId}]
                              </span>
                              <div className="flex-1">
                                <p className="font-medium">{citation.title}</p>
                                {citation.relevance && (
                                  <p className="text-blue-700 mt-0.5">
                                    {citation.relevance}
                                  </p>
                                )}
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

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
                <Loader2 className="size-4 animate-spin text-gray-500" />
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
