import * as React from "react";
import { useLocation, useNavigate } from "react-router";
import { LogOut, Shield, Upload, Library, GraduationCap, MessageSquareText } from "lucide-react";
import { Button } from "./ui/button";
import { cn } from "./ui/utils";
import { useAuth } from "../lib/auth-context";

type NavItem = {
  label: string;
  path: string;
  icon: React.ReactNode;
  adminOnly?: boolean;
};

export function AppHeader() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const navItems: NavItem[] = [
    { label: "文献问答", path: "/", icon: <MessageSquareText className="size-4" /> },
    { label: "学生工作区", path: "/workspace", icon: <GraduationCap className="size-4" /> },
    { label: "文献上传", path: "/documents/upload", icon: <Upload className="size-4" /> },
    { label: "文献管理", path: "/documents", icon: <Library className="size-4" /> },
    { label: "管理员", path: "/admin", icon: <Shield className="size-4" />, adminOnly: true },
  ];

  return (
    <div className="w-full border-b bg-white">
      <div className="mx-auto flex h-14 max-w-[1400px] items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <div className="size-8 rounded-lg bg-blue-600" />
            <div className="text-sm font-semibold text-gray-900">Research Copilot</div>
          </div>
          <div className="ml-4 hidden items-center gap-1 md:flex">
            {navItems
              .filter((i) => !i.adminOnly || user?.is_admin)
              .map((item) => {
                const active = location.pathname === item.path;
                return (
                  <Button
                    key={item.path}
                    variant={active ? "default" : "ghost"}
                    size="sm"
                    className={cn("gap-2", active ? "" : "text-gray-700")}
                    onClick={() => navigate(item.path)}
                  >
                    {item.icon}
                    {item.label}
                  </Button>
                );
              })}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden text-sm text-gray-600 md:block">
            {user ? (
              <>
                {user.username}
                {user.is_admin ? <span className="ml-2 rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-700">admin</span> : null}
              </>
            ) : null}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="gap-2"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            <LogOut className="size-4" />
            退出
          </Button>
        </div>
      </div>

      {/* Mobile nav */}
      <div className="mx-auto flex max-w-[1400px] gap-1 overflow-x-auto px-2 pb-2 md:hidden">
        {navItems
          .filter((i) => !i.adminOnly || user?.is_admin)
          .map((item) => {
            const active = location.pathname === item.path;
            return (
              <Button
                key={item.path}
                variant={active ? "default" : "outline"}
                size="sm"
                className="shrink-0 gap-2"
                onClick={() => navigate(item.path)}
              >
                {item.icon}
                {item.label}
              </Button>
            );
          })}
      </div>
    </div>
  );
}

