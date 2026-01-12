/**
 * DemoMarkdown Component
 * Renders markdown-like content for landing page tool demos
 * Supports: bold, code blocks, lists, emojis, line breaks
 */

'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, Copy } from 'lucide-react';

interface DemoMarkdownProps {
  content: string;
  isStreaming?: boolean;
}

export function DemoMarkdown({ content, isStreaming = false }: DemoMarkdownProps) {
  const renderContent = () => {
    const lines = content.split('\n');
    const elements: JSX.Element[] = [];
    let inCodeBlock = false;
    let codeContent = '';
    let codeLanguage = '';

    lines.forEach((line, index) => {
      // Code block start
      if (line.startsWith('```')) {
        if (!inCodeBlock) {
          inCodeBlock = true;
          codeLanguage = line.slice(3).trim();
          codeContent = '';
        } else {
          // Code block end
          inCodeBlock = false;
          elements.push(
            <CodeBlock key={`code-${index}`} code={codeContent.trim()} language={codeLanguage} />
          );
          codeContent = '';
          codeLanguage = '';
        }
        return;
      }

      if (inCodeBlock) {
        codeContent += line + '\n';
        return;
      }

      // Empty line
      if (line.trim() === '') {
        elements.push(<div key={`empty-${index}`} className="h-2" />);
        return;
      }

      // Headers
      if (line.startsWith('### ')) {
        elements.push(
          <h4 key={`h3-${index}`} className="text-white font-semibold text-sm mt-2 mb-1">
            {renderInlineStyles(line.slice(4))}
          </h4>
        );
        return;
      }

      if (line.startsWith('## ')) {
        elements.push(
          <h3 key={`h2-${index}`} className="text-white font-semibold mt-2 mb-1">
            {renderInlineStyles(line.slice(3))}
          </h3>
        );
        return;
      }

      // Bullet lists
      if (line.match(/^[-•] /)) {
        elements.push(
          <div key={`li-${index}`} className="flex items-start space-x-2 ml-1">
            <span className="text-emerald-400 mt-0.5">•</span>
            <span className="text-gray-200 text-sm">{renderInlineStyles(line.slice(2))}</span>
          </div>
        );
        return;
      }

      // Checkbox items
      if (line.match(/^- \[[ x]\] /)) {
        const isChecked = line.includes('[x]');
        const text = line.replace(/^- \[[ x]\] /, '');
        elements.push(
          <div key={`check-${index}`} className="flex items-start space-x-2 ml-1">
            <span className={`mt-0.5 ${isChecked ? 'text-emerald-400' : 'text-gray-500'}`}>
              {isChecked ? '☑' : '☐'}
            </span>
            <span className={`text-sm ${isChecked ? 'text-gray-400 line-through' : 'text-gray-200'}`}>
              {renderInlineStyles(text)}
            </span>
          </div>
        );
        return;
      }

      // Regular paragraph
      elements.push(
        <p key={`p-${index}`} className="text-gray-200 text-sm leading-relaxed">
          {renderInlineStyles(line)}
        </p>
      );
    });

    return elements;
  };

  // Render inline styles: **bold**, `code`, links
  const renderInlineStyles = (text: string): JSX.Element[] => {
    const parts: JSX.Element[] = [];
    let remaining = text;
    let keyIndex = 0;

    while (remaining.length > 0) {
      // Bold text **text**
      const boldMatch = remaining.match(/\*\*(.+?)\*\*/);
      // Inline code `code`
      const codeMatch = remaining.match(/`([^`]+)`/);

      // Find which comes first
      const boldIndex = boldMatch ? remaining.indexOf(boldMatch[0]) : Infinity;
      const codeIndex = codeMatch ? remaining.indexOf(codeMatch[0]) : Infinity;

      if (boldIndex === Infinity && codeIndex === Infinity) {
        // No more special formatting
        parts.push(<span key={`text-${keyIndex++}`}>{remaining}</span>);
        break;
      }

      if (boldIndex < codeIndex) {
        // Bold comes first
        if (boldIndex > 0) {
          parts.push(<span key={`text-${keyIndex++}`}>{remaining.slice(0, boldIndex)}</span>);
        }
        parts.push(
          <span key={`bold-${keyIndex++}`} className="font-semibold text-white">
            {boldMatch![1]}
          </span>
        );
        remaining = remaining.slice(boldIndex + boldMatch![0].length);
      } else {
        // Code comes first
        if (codeIndex > 0) {
          parts.push(<span key={`text-${keyIndex++}`}>{remaining.slice(0, codeIndex)}</span>);
        }
        parts.push(
          <code
            key={`code-${keyIndex++}`}
            className="bg-gray-700/60 text-emerald-300 px-1.5 py-0.5 rounded text-xs font-mono"
          >
            {codeMatch![1]}
          </code>
        );
        remaining = remaining.slice(codeIndex + codeMatch![0].length);
      }
    }

    return parts;
  };

  return (
    <div className="space-y-1">
      {renderContent()}
      {isStreaming && (
        <motion.span
          className="inline-block w-0.5 h-4 bg-emerald-400 ml-0.5 align-middle rounded-full"
          animate={{ opacity: [1, 0, 1] }}
          transition={{ duration: 0.8, repeat: Infinity }}
        />
      )}
    </div>
  );
}

// Code Block Component with Copy Button
function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative my-2 group">
      {/* Language badge */}
      {language && (
        <div className="absolute top-0 left-3 -translate-y-1/2 px-2 py-0.5 bg-gray-700 rounded text-[10px] text-gray-400 uppercase font-mono">
          {language}
        </div>
      )}

      {/* Copy button */}
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-1.5 bg-gray-700/80 hover:bg-gray-600 rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
        title="Copy code"
      >
        {copied ? (
          <Check className="w-3 h-3 text-emerald-400" />
        ) : (
          <Copy className="w-3 h-3 text-gray-400" />
        )}
      </button>

      {/* Code content */}
      <pre className="bg-gray-800/80 border border-gray-700/50 rounded-lg p-3 pt-4 overflow-x-auto">
        <code className="text-xs text-gray-300 font-mono leading-relaxed whitespace-pre">
          {code}
        </code>
      </pre>
    </div>
  );
}
