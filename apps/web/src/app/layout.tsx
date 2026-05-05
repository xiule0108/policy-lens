import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PolicyLens / 政研透镜",
  description: "Open-source policy and market research analysis workbench"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
