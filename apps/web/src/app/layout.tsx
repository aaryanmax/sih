import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChronoVision AI — Multimodal Video Search",
  description:
    "Production-grade semantic video search powered by ColQwen2 late-interaction embeddings, Qdrant MaxSim, and Gemini AI explanations.",
  keywords: ["video search", "ColPali", "ColQwen2", "MaxSim", "multimodal", "AI"],
  openGraph: {
    title: "ChronoVision AI",
    description: "Search any video moment by natural language",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans bg-void text-slate-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}

