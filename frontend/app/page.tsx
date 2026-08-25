import { ChatWindow } from "@/components/ChatWindow";
import type { RoleOption } from "@/lib/types";

const ROLE_OPTIONS: RoleOption[] = [
  { userId: "user-hr", label: "HR", department: "Human Resources" },
  { userId: "user-eng", label: "Engineering", department: "Engineering" },
  { userId: "user-fin", label: "Finance", department: "Finance" },
  { userId: "user-admin", label: "Admin", department: "Company-wide" },
];

export default function Page() {
  return (
    <main className="min-h-screen bg-mesh-gradient px-4 py-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <ChatWindow roleOptions={ROLE_OPTIONS} />
      </div>
    </main>
  );
}
