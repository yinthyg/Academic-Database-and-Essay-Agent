import { useState } from "react";
import { ConversationsSidebarNew } from "../components/conversations-sidebar-new";
import { ChatAreaNew } from "../components/chat-area-new";
import { PaperExplorerNew } from "../components/paper-explorer-new";
import { AppHeader } from "../components/app-header";

export function ResearchCopilot() {
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [selectedPaperId, setSelectedPaperId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="flex h-screen flex-col bg-white">
      <AppHeader />
      <div className="flex min-h-0 flex-1">
        {/* Left Sidebar - Conversations */}
        <ConversationsSidebarNew
          activeConversationId={activeConversationId}
          onConversationSelect={setActiveConversationId}
          onConversationsChange={() => setRefreshKey((prev) => prev + 1)}
        />

        {/* Center - Chat Area */}
        <ChatAreaNew conversationId={activeConversationId} key={`chat-${activeConversationId}-${refreshKey}`} />

        {/* Right Panel - Paper Explorer */}
        <PaperExplorerNew selectedPaperId={selectedPaperId} onPaperSelect={setSelectedPaperId} />
      </div>
    </div>
  );
}