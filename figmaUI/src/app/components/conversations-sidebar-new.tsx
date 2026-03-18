import { useEffect, useState } from "react";
import { Plus, MessageSquare, Home, LogOut, User, Upload, Library, Shield } from "lucide-react";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";
import { Link } from "react-router";
import { useAuth } from "../lib/auth-context";
import * as api from "../lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import { Input } from "./ui/input";
import { Label } from "./ui/label";

interface ConversationsSidebarProps {
  activeConversationId: number | null;
  onConversationSelect: (id: number) => void;
  onConversationsChange: () => void;
}

export function ConversationsSidebarNew({
  activeConversationId,
  onConversationSelect,
  onConversationsChange,
}: ConversationsSidebarProps) {
  const { token, user, logout } = useAuth();
  const [conversations, setConversations] = useState<api.Conversation[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    loadConversations();
  }, [token]);

  const loadConversations = async () => {
    if (!token) return;
    try {
      const data = await api.getConversations(token);
      setConversations(data);
      
      // Auto-select first conversation if none selected
      if (!activeConversationId && data.length > 0) {
        onConversationSelect(data[0].id);
      }
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  };

  const handleCreateConversation = async () => {
    if (!token) return;
    setIsCreating(true);

    try {
      const newConv = await api.createConversation(token, {
        title: newTitle || undefined,
      });
      await loadConversations();
      onConversationSelect(newConv.id);
      onConversationsChange();
      setNewTitle("");
      setIsDialogOpen(false);
    } catch (error) {
      console.error("Failed to create conversation:", error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="w-64 border-r border-gray-200 flex flex-col bg-gray-50">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <Link to="/">
          <h1 className="text-lg font-semibold text-gray-900 mb-1">Research Copilot</h1>
        </Link>
        <p className="text-xs text-gray-500">AI Research Assistant</p>
      </div>

      {/* User Info */}
      <div className="p-3 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            <User className="size-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user?.username}</p>
            <p className="text-xs text-gray-500">
              {user?.is_admin ? "Admin" : "User"}
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="w-full justify-start gap-2"
          onClick={logout}
        >
          <LogOut className="size-4" />
          Logout
        </Button>
      </div>

      {/* Navigation */}
      <div className="p-3 border-b border-gray-200 bg-white">
        <div className="space-y-2">
          <Link to="/workspace">
            <Button variant="outline" size="sm" className="w-full justify-start gap-2">
              <Home className="size-4" />
              学生工作区
            </Button>
          </Link>
          <Link to="/documents/upload">
            <Button variant="outline" size="sm" className="w-full justify-start gap-2">
              <Upload className="size-4" />
              文献上传
            </Button>
          </Link>
          <Link to="/documents">
            <Button variant="outline" size="sm" className="w-full justify-start gap-2">
              <Library className="size-4" />
              文献管理
            </Button>
          </Link>
          {user?.is_admin ? (
            <Link to="/admin">
              <Button variant="outline" size="sm" className="w-full justify-start gap-2">
                <Shield className="size-4" />
                管理员后台
              </Button>
            </Link>
          ) : null}
        </div>
      </div>

      {/* New Conversation Button */}
      <div className="p-3">
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="w-full justify-start gap-2" variant="default">
              <Plus className="size-4" />
              New Conversation
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Conversation</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="title">Title (Optional)</Label>
                <Input
                  id="title"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g., Deep Learning Research"
                />
              </div>
              <Button
                onClick={handleCreateConversation}
                disabled={isCreating}
                className="w-full"
              >
                {isCreating ? "Creating..." : "Create"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Conversations List */}
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-2">
          {conversations.map((conv) => (
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
                  {conv.title || `Conversation ${conv.id}`}
                </h3>
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {conv.collection_id && (
                  <Badge variant="secondary" className="text-xs">
                    Collection: {conv.collection_id}
                  </Badge>
                )}
                {conv.student_paper_id && (
                  <Badge variant="outline" className="text-xs">
                    Paper: {conv.student_paper_id}
                  </Badge>
                )}
              </div>
              <p className="text-xs text-gray-400 mt-2">
                {new Date(conv.created_at).toLocaleDateString()}
              </p>
            </button>
          ))}

          {conversations.length === 0 && (
            <div className="text-center py-8">
              <p className="text-sm text-gray-500">No conversations yet</p>
              <p className="text-xs text-gray-400 mt-1">Create one to get started</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
