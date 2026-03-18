import { useState, useEffect } from "react";

interface StreamingTextProps {
  text: string;
  speed?: number;
}

export function StreamingText({ text, speed = 20 }: StreamingTextProps) {
  const [displayedText, setDisplayedText] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText((prev) => prev + text[currentIndex]);
        setCurrentIndex((prev) => prev + 1);
      }, speed);

      return () => clearTimeout(timer);
    }
  }, [currentIndex, text, speed]);

  return (
    <p className="text-sm text-gray-900 leading-relaxed whitespace-pre-wrap">
      {displayedText}
      {currentIndex < text.length && (
        <span className="inline-block w-1 h-4 bg-gray-900 ml-0.5 animate-pulse" />
      )}
    </p>
  );
}
