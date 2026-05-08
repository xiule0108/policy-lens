import { AppShell } from "@/components/AppShell";
import { ProjectWorkbench } from "@/components/ProjectWorkbench";

export default async function ProjectWorkspacePage({
  params
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;

  return (
    <AppShell>
      <ProjectWorkbench projectId={projectId} />
    </AppShell>
  );
}
