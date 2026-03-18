import { Navigate } from "react-router";
import { useAuth } from "../lib/auth-context";

export function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  if (!user?.is_admin) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

