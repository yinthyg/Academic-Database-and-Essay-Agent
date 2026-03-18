import { useState } from "react";
import { StudentPapersSidebarNew } from "../components/student-papers-sidebar-new";
import { PaperEditorNew } from "../components/paper-editor-new";
import { AiMentorNew } from "../components/ai-mentor-new";
import { AppHeader } from "../components/app-header";

export function StudentWorkspace() {
  const [activePaperId, setActivePaperId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="flex h-screen flex-col bg-white">
      <AppHeader />
      <div className="flex min-h-0 flex-1">
        {/* Left Sidebar - Student Papers */}
        <StudentPapersSidebarNew
          activePaperId={activePaperId}
          onPaperSelect={setActivePaperId}
          onPapersChange={() => setRefreshKey((prev) => prev + 1)}
        />

        {/* Center - Paper Editor */}
        <PaperEditorNew paperId={activePaperId} key={`editor-${activePaperId}-${refreshKey}`} />

        {/* Right Panel - AI Mentor */}
        <AiMentorNew paperId={activePaperId} key={`mentor-${activePaperId}`} />
      </div>
    </div>
  );
}