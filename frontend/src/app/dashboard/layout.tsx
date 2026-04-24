import { AuthGuard } from "@/components/auth/AuthGuard";
import MainLayout from "@/components/layout/MainLayout";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <MainLayout>{children}</MainLayout>
    </AuthGuard>
  );
}
