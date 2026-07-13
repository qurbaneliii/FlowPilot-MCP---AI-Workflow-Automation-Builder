import { RunDetailClient } from "./RunDetailClient";

export const dynamicParams = false;

export function generateStaticParams() {
  return [{ runId: "demo" }];
}

type RunDetailPageProps = {
  params: Promise<{
    runId: string;
  }>;
};

export default async function RunDetailPage({ params }: RunDetailPageProps) {
  const { runId } = await params;
  return <RunDetailClient runId={runId} />;
}
