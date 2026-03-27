"use client";

import { useRouter } from "next/navigation";

export default function LabUploadPage() {
  const router = useRouter();

  return (
    <div className="flex flex-col min-h-screen items-center justify-center px-6 text-center">
      <div className="w-20 h-20 bg-blue-600/10 rounded-full flex items-center justify-center mb-6">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-blue-500">
          <path fillRule="evenodd" d="M11.47 2.47a.75.75 0 0 1 1.06 0l4.5 4.5a.75.75 0 0 1-1.06 1.06l-3.22-3.22V16.5a.75.75 0 0 1-1.5 0V4.81L8.03 8.03a.75.75 0 0 1-1.06-1.06l4.5-4.5ZM3 15.75a.75.75 0 0 1 .75.75v2.25a1.5 1.5 0 0 0 1.5 1.5h13.5a1.5 1.5 0 0 0 1.5-1.5V16.5a.75.75 0 0 1 1.5 0v2.25a3 3 0 0 1-3 3H5.25a3 3 0 0 1-3-3V16.5a.75.75 0 0 1 .75-.75Z" clipRule="evenodd" />
        </svg>
      </div>
      <h1 className="text-xl font-bold mb-2">Lab Upload Coming Soon</h1>
      <p className="text-gray-500 text-sm leading-relaxed max-w-xs">
        Uploading blood work directly from PDFs and images will be available in the next release. For now, ask Otto to enter your results via the chat.
      </p>
      <button
        onClick={() => router.back()}
        className="mt-8 px-6 py-3 bg-[#1a1a1a] border border-gray-800 rounded-xl text-sm font-medium hover:bg-gray-800 transition-colors"
      >
        Go Back
      </button>
    </div>
  );
}
