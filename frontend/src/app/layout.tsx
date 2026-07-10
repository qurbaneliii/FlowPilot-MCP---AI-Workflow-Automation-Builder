import type { Metadata } from "next";
import "reactflow/dist/style.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "FlowPilot MCP | AI Workflow Automation Builder",
  description:
    "Turn natural language automation requests into executable workflow graphs."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
