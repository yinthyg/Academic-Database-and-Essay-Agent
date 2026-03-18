import { useState } from "react";
import { Send, Sparkles, BookOpen, Plus } from "lucide-react";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";

interface MentorMessage {
  id: string;
  role: "user" | "mentor";
  content: string;
  suggestions?: CitationSuggestion[];
  messageType?: "advice" | "citation";
}

interface CitationSuggestion {
  paperId: string;
  title: string;
  authors: string;
  relevance: string;
}

const mockMessages: MentorMessage[] = [
  {
    id: "msg-1",
    role: "user",
    content: "Can you suggest some recent papers on transformer architectures?",
  },
  {
    id: "msg-2",
    role: "mentor",
    content:
      "Based on your paper's focus on transformers, I recommend these highly relevant papers:",
    messageType: "citation",
    suggestions: [
      {
        paperId: "paper:12",
        title: "Attention Is All You Need",
        authors: "Vaswani et al., 2017",
        relevance: "Foundational transformer paper - essential citation",
      },
      {
        paperId: "paper:45",
        title: "BERT: Pre-training of Deep Bidirectional Transformers",
        authors: "Devlin et al., 2018",
        relevance: "Key advancement in bidirectional transformers",
      },
      {
        paperId: "paper:78",
        title: "Scaling Laws for Neural Language Models",
        authors: "Kaplan et al., 2020",
        relevance: "Important for understanding model scaling",
      },
    ],
  },
];

interface AiMentorProps {
  paperId: string;
}

export function AiMentor({ paperId }: AiMentorProps) {
  const [messages, setMessages] = useState<MentorMessage[]>(mockMessages);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: MentorMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    // Simulate AI response
    setTimeout(() => {
      const mentorMessage: MentorMessage = {
        id: `msg-${Date.now()}-ai`,
        role: "mentor",
        content:
          "That's a great question! Here's my advice: Consider structuring this section with a clear progression from problem statement to your proposed solution. Make sure to highlight the novelty of your approach.",
        messageType: "advice",
      };
      setMessages((prev) => [...prev, mentorMessage]);
    }, 1000);
  };

  const handleInsertCitation = (citation: CitationSuggestion) => {
    // In a real app, this would insert the citation into the editor
    console.log("Inserting citation:", citation);
  };

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
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] ${message.role === "user" ? "bg-purple-600 text-white rounded-xl rounded-tr-sm px-3 py-2" : "space-y-3"}`}>
                {message.role === "user" ? (
                  <p className="text-sm leading-relaxed">{message.content}</p>
                ) : (
                  <>
                    {/* Message Type Badge */}
                    {message.messageType && (
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={message.messageType === "citation" ? "default" : "secondary"}
                          className="text-xs"
                        >
                          {message.messageType === "citation" ? (
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
                    )}

                    {/* Mentor Message */}
                    <div className="bg-white border border-gray-200 rounded-xl rounded-tl-sm px-3 py-2 shadow-sm">
                      <p className="text-sm text-gray-900 leading-relaxed">
                        {message.content}
                      </p>
                    </div>

                    {/* Citation Suggestions */}
                    {message.suggestions && message.suggestions.length > 0 && (
                      <div className="space-y-2">
                        {message.suggestions.map((suggestion, idx) => (
                          <div
                            key={idx}
                            className="bg-white border border-purple-200 rounded-lg p-3 space-y-2"
                          >
                            <div>
                              <h4 className="text-sm font-medium text-gray-900 mb-1">
                                {suggestion.title}
                              </h4>
                              <p className="text-xs text-gray-600 mb-1">
                                {suggestion.authors}
                              </p>
                              <p className="text-xs text-purple-700 italic">
                                {suggestion.relevance}
                              </p>
                            </div>
                            <Button
                              size="sm"
                              variant="outline"
                              className="w-full justify-center gap-2 text-xs"
                              onClick={() => handleInsertCitation(suggestion)}
                            >
                              <Plus className="size-3" />
                              Insert Citation
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* Quick Actions */}
      <div className="px-4 py-2 border-t border-gray-200 bg-white">
        <div className="flex gap-2 mb-3">
          <Button
            size="sm"
            variant="outline"
            className="text-xs flex-1"
            onClick={() =>
              setInput("Can you review my introduction section?")
            }
          >
            Review Section
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="text-xs flex-1"
            onClick={() =>
              setInput("Suggest citations for methodology")
            }
          >
            Find Citations
          </Button>
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
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim()}
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
