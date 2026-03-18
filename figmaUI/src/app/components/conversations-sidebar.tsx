import { Plus, MessageSquare, Home } from "lucide-react";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";
import { Link } from "react-router";

interface Conversation {
  id: string;
  title: string;
  collectionId?: string;
  studentPaperId?: string;
  timestamp: string;
}

const mockConversations: Conversation[] = [
  {
    id: "conv-1",
    title: "Deep Learning Architectures",
    collectionId: "ml-papers",
    timestamp: "2026-03-17",
  },
  {
    id: "conv-2",
    title: "Transformer Models Survey",
    studentPaperId: "paper-1",
    timestamp: "2026-03-16",
  },
  {
    id: "conv-3",
    title: "RAG Implementation Strategies",
    timestamp: "2026-03-15",
  },
  {
    id: "conv-4",
    title: "Multi-modal Learning",
    collectionId: "vision-papers",
    timestamp: "2026-03-14",
  },
];

interface ConversationsSidebarProps {
  activeConversationId: string;
  onConversationSelect: (id: string) => void;
}

export function ConversationsSidebar({
  activeConversationId,
  onConversationSelect,
}: ConversationsSidebarProps) {
  return (
    <div className="w-64 border-r border-gray-200 flex flex-col bg-gray-50">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <Link to="/">
          <h1 className="text-lg font-semibold text-gray-900 mb-1">Research Copilot</h1>
        </Link>
        <p className="text-xs text-gray-500">AI Research Assistant</p>
      </div>

      {/* Navigation */}
      <div className="p-3 border-b border-gray-200 bg-white">
        <Link to="/workspace">
          <Button variant="outline" size="sm" className="w-full justify-start gap-2">
            <Home className="size-4" />
            Student Workspace
          </Button>
        </Link>
      </div>

      {/* New Conversation Button */}
      <div className="p-3">
        <Button className="w-full justify-start gap-2" variant="default">
          <Plus className="size-4" />
          New Conversation
        </Button>
      </div>

      {/* Conversations List */}
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-2">
          {mockConversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => onConversationSelect(conv.id)}
              className={`w-full text-left p-3 rounded-lg border transition-all ${
                activeConversationId === conv.id
                  ? "bg-white border-blue-200 shadow-sm"
                  : "bg-white border-gray-200 hover:border-gray-300 hover:shadow-sm"
              }`}
            >
              <div className="flex items-start gap-2 mb-2">
                <MessageSquare className="size-4 text-gray-400 mt-0.5 flex-shrink-0" />
                <h3 className="text-sm font-medium text-gray-900 line-clamp-2">
                  {conv.title}
                </h3>
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {conv.collectionId && (
                  <Badge variant="secondary" className="text-xs">
                    {conv.collectionId}
                  </Badge>
                )}
                {conv.studentPaperId && (
                  <Badge variant="outline" className="text-xs">
                    Draft: {conv.studentPaperId}
                  </Badge>
                )}
              </div>
              <p className="text-xs text-gray-400 mt-2">{conv.timestamp}</p>
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
