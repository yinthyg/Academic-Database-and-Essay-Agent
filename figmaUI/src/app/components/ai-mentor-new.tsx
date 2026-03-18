import { useState, useEffect, useRef } from "react";
import { Send, Sparkles, BookOpen, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";
import { useAuth } from "../lib/auth-context";
import * as api from "../lib/api";

interface MentorMessage {
  id: string;
  role: "user" | "mentor";
  content: string;
  citations?: string[];
  timestamp: Date;
}

interface AiMentorNewProps {
  paperId: number | null;
}

export function AiMentorNew({ paperId }: AiMentorNewProps) {
  const { token } = useAuth();
  const [messages, setMessages] = useState<MentorMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Clear messages when paper changes
    setMessages([]);
  }, [paperId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (customInput?: string) => {
    const question = customInput || input;
    if (!question.trim() || isLoading || !token || !paperId) return;

    const userMessage: MentorMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: question,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await api.mentorChat(token, paperId, question);
      
      const mentorMessage: MentorMessage = {
        id: `mentor-${Date.now()}`,
        role: "mentor",
        content: response.answer,
        citations: response.citations,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, mentorMessage]);
    } catch (error) {
      console.error("Failed to get mentor response:", error);
      
      const errorMessage: MentorMessage = {
        id: `error-${Date.now()}`,
        role: "mentor",
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : "Unknown error"}`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickActions = [
    { label: "Review Section", prompt: "Can you review my latest section?" },
    { label: "Find Citations", prompt: "Suggest relevant citations for my paper" },
    { label: "Improve Writing", prompt: "How can I improve my writing style?" },
  ];

  if (!paperId) {
    return (
      <div className="w-96 border-l border-gray-200 flex items-center justify-center bg-gradient-to-b from-purple-50 to-white">
        <div className="text-center px-4">
          <Sparkles className="size-8 text-purple-600 mx-auto mb-2" />
          <p className="text-sm text-gray-500">Select a paper to get AI assistance</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-96 border-l border-gray-200 flex flex-col bg-gradient-to-b from-purple-50 to-white">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="size-5 text-purple-600" />
          <h2 className="text-lg font-semibold text-gray-900">AI Mentor</h2>
        </div>
        <p className="text-sm text-gray-500">Writing feedback & citations</p>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-8">
              <Sparkles className="size-8 text-purple-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600 font-medium">How can I help you today?</p>
              <p className="text-xs text-gray-500 mt-1">
                Ask for writing feedback or citation suggestions
              </p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] ${
                  message.role === "user"
                    ? "bg-purple-600 text-white rounded-xl rounded-tr-sm px-3 py-2"
                    : "space-y-3"
                }`}
              >
                {message.role === "user" ? (
                  <p className="text-sm leading-relaxed">{message.content}</p>
                ) : (
                  <>
                    {/* Message Type Badge */}
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={message.citations && message.citations.length > 0 ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {message.citations && message.citations.length > 0 ? (
                          <>
                            <BookOpen className="size-3 mr-1" />
                            Citations
                          </>
                        ) : (
                          <>
                            <Sparkles className="size-3 mr-1" />
                            Advice
                          </>
                        )}
                      </Badge>
                    </div>

                    {/* Mentor Message */}
                    <div className="bg-white border border-gray-200 rounded-xl rounded-tl-sm px-3 py-2 shadow-sm">
                      <p className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">
                        {message.content}
                      </p>
                    </div>

                    {/* Citations */}
                    {message.citations && message.citations.length > 0 && (
                      <div className="space-y-2">
                        {message.citations.map((citation, idx) => (
                          <div
                            key={idx}
                            className="bg-white border border-purple-200 rounded-lg p-3"
                          >
                            <p className="text-sm text-gray-900 leading-relaxed">
                              {citation}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-xl rounded-tl-sm px-4 py-3">
                <Loader2 className="size-4 animate-spin text-purple-600" />
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Quick Actions */}
      <div className="px-4 py-2 border-t border-gray-200 bg-white">
        <div className="grid grid-cols-2 gap-2 mb-3">
          {quickActions.map((action) => (
            <Button
              key={action.label}
              size="sm"
              variant="outline"
              className="text-xs h-auto py-2"
              onClick={() => handleSend(action.prompt)}
              disabled={isLoading}
            >
              {action.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask for writing feedback, experiments, or citations..."
            className="flex-1 min-h-[60px] text-sm resize-none"
            disabled={isLoading}
          />
          <Button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            size="lg"
            className="px-4"
          >
            <Send className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
