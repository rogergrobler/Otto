import type { Metadata } from "next";
import "./globals.css";
import { BottomNav } from "@/components/nav";

export const metadata: Metadata = {
  title: "Otto — Digital Health Twin",
  description: "Your personal digital health twin powered by AI",
  viewport: "width=device-width, initial-scale=1, maximum-scale=1",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#0a0a0a] text-white min-h-screen">
        <main className="max-w-md mx-auto pb-20 min-h-screen">
          {children}
        </main>
        <BottomNav />
      </body>
    </html>
  );
}
