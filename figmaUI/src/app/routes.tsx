import { createBrowserRouter } from "react-router";
import { ResearchCopilot } from "./pages/research-copilot";
import { StudentWorkspace } from "./pages/student-workspace";
import { Login } from "./pages/login";
import { ProtectedRoute } from "./pages/protected-route";
import { DocumentUpload } from "./pages/document-upload";
import { Documents } from "./pages/documents";
import { DocumentDetail } from "./pages/document-detail";
import { Admin } from "./pages/admin";
import { AdminRoute } from "./pages/admin-route";

export const router = createBrowserRouter([
  {
    path: "/login",
    Component: Login,
  },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <ResearchCopilot />
      </ProtectedRoute>
    ),
  },
  {
    path: "/workspace",
    element: (
      <ProtectedRoute>
        <StudentWorkspace />
      </ProtectedRoute>
    ),
  },
  {
    path: "/documents/upload",
    element: (
      <ProtectedRoute>
        <DocumentUpload />
      </ProtectedRoute>
    ),
  },
  {
    path: "/documents",
    element: (
      <ProtectedRoute>
        <Documents />
      </ProtectedRoute>
    ),
  },
  {
    path: "/documents/:documentId",
    element: (
      <ProtectedRoute>
        <DocumentDetail />
      </ProtectedRoute>
    ),
  },
  {
    path: "/admin",
    element: (
      <ProtectedRoute>
        <AdminRoute>
          <Admin />
        </AdminRoute>
      </ProtectedRoute>
    ),
  },
]);