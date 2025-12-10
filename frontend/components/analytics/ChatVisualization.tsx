/**
 * ChatVisualization Component
 *
 * Parses AI responses and renders appropriate visualizations
 * alongside the text response.
 */

'use client';

import { useMemo } from 'react';
import SimpleLineChart from './SimpleLineChart';
import SimpleBarChart from './SimpleBarChart';
import MetricCard from './MetricCard';

interface VisualizationData {
  type: 'metrics' | 'bar-chart' | 'line-chart' | 'table';
  title?: string;
  data: any;
}

interface ChatVisualizationProps {
  content: string;
  role: 'user' | 'assistant';
}

// Extract metrics from text (e.g., "Total Revenue: $5,000" or "15 items")
function extractMetrics(text: string): { title: string; value: string; icon?: string }[] {
  const metrics: { title: string; value: string; icon?: string }[] = [];

  // Pattern: "Label: $X,XXX" or "Label: X%"
  const metricPatterns = [
    /(?:total|revenue|sales|amount|value|profit|cost)[:\s]+\$?([\d,]+(?:\.\d{2})?)/gi,
    /(?:items?|products?|units?|orders?|customers?)[:\s]+([\d,]+)/gi,
    /([\d,]+(?:\.\d{1,2})?)\s*%\s*(?:increase|decrease|growth|change)/gi,
  ];

  // Look for specific metrics
  const salesMatch = text.match(/(?:total\s+)?(?:revenue|sales)[:\s]*\$?([\d,]+(?:\.\d{2})?)/i);
  if (salesMatch) {
    metrics.push({
      title: 'Total Sales',
      value: salesMatch[1].includes('$') ? salesMatch[1] : `$${salesMatch[1]}`,
      icon: '💰',
    });
  }

  const itemsMatch = text.match(/(\d+)\s*(?:items?|products?)/i);
  if (itemsMatch) {
    metrics.push({
      title: 'Items',
      value: itemsMatch[1],
      icon: '📦',
    });
  }

  const ordersMatch = text.match(/(\d+)\s*(?:orders?|transactions?)/i);
  if (ordersMatch) {
    metrics.push({
      title: 'Orders',
      value: ordersMatch[1],
      icon: '🛒',
    });
  }

  const percentMatch = text.match(/([\d.]+)%\s*(?:increase|growth|up)/i);
  if (percentMatch) {
    metrics.push({
      title: 'Growth',
      value: `+${percentMatch[1]}%`,
      icon: '📈',
    });
  }

  const decreaseMatch = text.match(/([\d.]+)%\s*(?:decrease|down|drop)/i);
  if (decreaseMatch) {
    metrics.push({
      title: 'Change',
      value: `-${decreaseMatch[1]}%`,
      icon: '📉',
    });
  }

  return metrics;
}

// Extract bar chart data from text (e.g., product rankings, categories)
function extractBarData(text: string): { label: string; value: number }[] {
  const data: { label: string; value: number }[] = [];

  // Pattern: "1. Product Name - $X,XXX" or "Product: $X,XXX"
  const listPattern = /(?:\d+\.\s*)?([A-Za-z][A-Za-z0-9\s]+?)(?:\s*[-:]\s*)\$?([\d,]+(?:\.\d{2})?)/g;
  let match;

  while ((match = listPattern.exec(text)) !== null) {
    const label = match[1].trim();
    const value = parseFloat(match[2].replace(/,/g, ''));
    if (!isNaN(value) && label.length > 0 && label.length < 50) {
      data.push({ label, value });
    }
  }

  // Also try bullet points: "• Item Name: value"
  const bulletPattern = /[•\-\*]\s*([A-Za-z][A-Za-z0-9\s]+?):\s*\$?([\d,]+(?:\.\d{2})?)/g;
  while ((match = bulletPattern.exec(text)) !== null) {
    const label = match[1].trim();
    const value = parseFloat(match[2].replace(/,/g, ''));
    if (!isNaN(value) && label.length > 0 && label.length < 50) {
      // Avoid duplicates
      if (!data.find(d => d.label === label)) {
        data.push({ label, value });
      }
    }
  }

  return data.slice(0, 8); // Max 8 items
}

// Extract trend/time series data
function extractLineData(text: string): { label: string; value: number }[] {
  const data: { label: string; value: number }[] = [];

  // Pattern: "Day X: $Y" or "Jan: $Y" or date-like patterns
  const datePatterns = [
    /(?:day\s*)?(\d{1,2})(?:st|nd|rd|th)?[:\s]+\$?([\d,]+(?:\.\d{2})?)/gi,
    /(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[:\s]+\$?([\d,]+(?:\.\d{2})?)/gi,
    /(monday|tuesday|wednesday|thursday|friday|saturday|sunday)[:\s]+\$?([\d,]+(?:\.\d{2})?)/gi,
    /week\s*(\d+)[:\s]+\$?([\d,]+(?:\.\d{2})?)/gi,
  ];

  for (const pattern of datePatterns) {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      const label = match[1];
      const value = parseFloat(match[2].replace(/,/g, ''));
      if (!isNaN(value)) {
        data.push({ label, value });
      }
    }
    if (data.length > 0) break; // Use first matching pattern
  }

  return data.slice(0, 30); // Max 30 points
}

// Detect visualization type based on content
function detectVisualizationType(text: string): 'metrics' | 'bar-chart' | 'line-chart' | 'none' {
  const lowerText = text.toLowerCase();

  // Keywords that suggest different chart types
  const trendKeywords = ['trend', 'over time', 'daily', 'weekly', 'monthly', 'last \d+ days', 'growth'];
  const comparisonKeywords = ['top', 'best', 'worst', 'ranking', 'compare', 'products', 'categories'];
  const summaryKeywords = ['total', 'summary', 'overview', 'revenue', 'sales'];

  // Check for trends first (line chart)
  if (trendKeywords.some(k => new RegExp(k).test(lowerText))) {
    const lineData = extractLineData(text);
    if (lineData.length >= 3) return 'line-chart';
  }

  // Check for comparisons (bar chart)
  if (comparisonKeywords.some(k => lowerText.includes(k))) {
    const barData = extractBarData(text);
    if (barData.length >= 2) return 'bar-chart';
  }

  // Check for summary metrics
  if (summaryKeywords.some(k => lowerText.includes(k))) {
    const metrics = extractMetrics(text);
    if (metrics.length > 0) return 'metrics';
  }

  // Try extracting data anyway
  const barData = extractBarData(text);
  if (barData.length >= 3) return 'bar-chart';

  const metrics = extractMetrics(text);
  if (metrics.length >= 2) return 'metrics';

  return 'none';
}

export default function ChatVisualization({ content, role }: ChatVisualizationProps) {
  const visualization = useMemo(() => {
    if (role === 'user') return null;

    const vizType = detectVisualizationType(content);

    switch (vizType) {
      case 'metrics': {
        const metrics = extractMetrics(content);
        if (metrics.length === 0) return null;
        return {
          type: 'metrics' as const,
          data: metrics,
        };
      }
      case 'bar-chart': {
        const data = extractBarData(content);
        if (data.length === 0) return null;
        return {
          type: 'bar-chart' as const,
          title: content.toLowerCase().includes('top') ? 'Top Items' : 'Comparison',
          data,
        };
      }
      case 'line-chart': {
        const data = extractLineData(content);
        if (data.length === 0) return null;
        return {
          type: 'line-chart' as const,
          title: 'Trend',
          data,
        };
      }
      default:
        return null;
    }
  }, [content, role]);

  // Render text content with markdown-like formatting
  const renderContent = () => {
    // Split content into paragraphs
    const paragraphs = content.split('\n\n');

    return paragraphs.map((para, idx) => {
      // Handle bullet points
      if (para.includes('\n- ') || para.includes('\n• ') || para.startsWith('- ') || para.startsWith('• ')) {
        const lines = para.split('\n');
        return (
          <ul key={idx} className="list-disc list-inside space-y-1 my-2">
            {lines.map((line, lineIdx) => {
              const cleanLine = line.replace(/^[\-•]\s*/, '').trim();
              if (!cleanLine) return null;
              return <li key={lineIdx}>{cleanLine}</li>;
            })}
          </ul>
        );
      }

      // Handle numbered lists
      if (/^\d+\.\s/.test(para)) {
        const lines = para.split('\n');
        return (
          <ol key={idx} className="list-decimal list-inside space-y-1 my-2">
            {lines.map((line, lineIdx) => {
              const cleanLine = line.replace(/^\d+\.\s*/, '').trim();
              if (!cleanLine) return null;
              return <li key={lineIdx}>{cleanLine}</li>;
            })}
          </ol>
        );
      }

      // Handle bold text (**text** or __text__)
      const formattedPara = para
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/__(.+?)__/g, '<strong>$1</strong>');

      return (
        <p
          key={idx}
          className="my-1"
          dangerouslySetInnerHTML={{ __html: formattedPara }}
        />
      );
    });
  };

  return (
    <div className="space-y-3">
      {/* Text Content */}
      <div className="text-sm whitespace-pre-wrap">
        {renderContent()}
      </div>

      {/* Visualization */}
      {visualization && (
        <div className="mt-3 border-t border-gray-100 pt-3">
          {visualization.type === 'metrics' && (
            <div className="grid grid-cols-2 gap-2">
              {visualization.data.map((metric: any, idx: number) => (
                <MetricCard
                  key={idx}
                  title={metric.title}
                  value={metric.value}
                  icon={metric.icon}
                />
              ))}
            </div>
          )}

          {visualization.type === 'bar-chart' && (
            <SimpleBarChart
              data={visualization.data}
              title={visualization.title}
              formatValue={(v) => v >= 1000 ? `$${(v / 1000).toFixed(1)}k` : `$${v}`}
            />
          )}

          {visualization.type === 'line-chart' && (
            <SimpleLineChart
              data={visualization.data}
              title={visualization.title}
              height={100}
              formatValue={(v) => v >= 1000 ? `$${(v / 1000).toFixed(1)}k` : `$${v}`}
            />
          )}
        </div>
      )}
    </div>
  );
}
