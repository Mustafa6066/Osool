'use client';

import React, { useRef, useCallback, useEffect, useState } from 'react';

// ═══════════════════════════════════════════════════════════
// VirtualMessageList — Windowed rendering for long chat histories
// Inspired by src/components/VirtualMessageList (Claude Code)
//
// Renders only visible messages + buffer, preventing performance
// degradation at scale (100s of messages).
// ═══════════════════════════════════════════════════════════

interface VirtualMessageListProps<T> {
  items: T[];
  estimatedItemHeight?: number;
  overscan?: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  getItemKey: (item: T, index: number) => string;
  className?: string;
  /** Auto-scroll to bottom when new items are added */
  autoScroll?: boolean;
  /** Callback when user scrolls away from bottom */
  onScrollAwayFromBottom?: (isAway: boolean) => void;
}

interface ItemMeasurement {
  offset: number;
  height: number;
}

export function VirtualMessageList<T>({
  items,
  estimatedItemHeight = 120,
  overscan = 3,
  renderItem,
  getItemKey,
  className = '',
  autoScroll = true,
  onScrollAwayFromBottom,
}: VirtualMessageListProps<T>) {
  const containerRef = useRef<HTMLDivElement>(null);
  const measurementCacheRef = useRef<Map<string, number>>(new Map());
  const [measurements, setMeasurements] = useState<ItemMeasurement[]>([]);
  const [scrollTop, setScrollTop] = useState(0);
  const [containerHeight, setContainerHeight] = useState(0);
  const isNearBottomRef = useRef(true);
  const prevItemCountRef = useRef(0);

  // Calculate measurements based on cached heights
  useEffect(() => {
    const newMeasurements: ItemMeasurement[] = [];
    let offset = 0;
    for (let i = 0; i < items.length; i++) {
      const key = getItemKey(items[i], i);
      const height = measurementCacheRef.current.get(key) ?? estimatedItemHeight;
      newMeasurements.push({ offset, height });
      offset += height;
    }
    setMeasurements(newMeasurements);
  }, [items, estimatedItemHeight, getItemKey]);

  // Auto-scroll when new items are added
  useEffect(() => {
    if (autoScroll && isNearBottomRef.current && items.length > prevItemCountRef.current) {
      requestAnimationFrame(() => {
        const el = containerRef.current;
        if (el) {
          el.scrollTop = el.scrollHeight;
        }
      });
    }
    prevItemCountRef.current = items.length;
  }, [items.length, autoScroll]);

  // Observe container resizes
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerHeight(entry.contentRect.height);
      }
    });
    observer.observe(el);
    setContainerHeight(el.clientHeight);

    return () => observer.disconnect();
  }, []);

  // Handle scroll
  const handleScroll = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    setScrollTop(el.scrollTop);

    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
    const wasNearBottom = isNearBottomRef.current;
    isNearBottomRef.current = isNearBottom;

    if (wasNearBottom !== isNearBottom) {
      onScrollAwayFromBottom?.(!isNearBottom);
    }
  }, [onScrollAwayFromBottom]);

  // Calculate visible range
  const totalHeight = measurements.length > 0
    ? measurements[measurements.length - 1].offset + measurements[measurements.length - 1].height
    : items.length * estimatedItemHeight;

  let startIndex = 0;
  let endIndex = items.length - 1;

  if (measurements.length > 0) {
    // Binary search for start index
    let lo = 0;
    let hi = measurements.length - 1;
    while (lo <= hi) {
      const mid = Math.floor((lo + hi) / 2);
      if (measurements[mid].offset + measurements[mid].height < scrollTop) {
        lo = mid + 1;
      } else {
        hi = mid - 1;
      }
    }
    startIndex = Math.max(0, lo - overscan);

    // Find end index
    const viewEnd = scrollTop + containerHeight;
    lo = startIndex;
    hi = measurements.length - 1;
    while (lo <= hi) {
      const mid = Math.floor((lo + hi) / 2);
      if (measurements[mid].offset < viewEnd) {
        lo = mid + 1;
      } else {
        hi = mid - 1;
      }
    }
    endIndex = Math.min(items.length - 1, lo + overscan);
  }

  // For small lists, skip virtualization entirely
  const shouldVirtualize = items.length > 20;

  // Measure rendered items
  const measureRef = useCallback(
    (el: HTMLDivElement | null, key: string) => {
      if (!el) return;
      const height = el.getBoundingClientRect().height;
      const cached = measurementCacheRef.current.get(key);
      if (cached !== height) {
        measurementCacheRef.current.set(key, height);
        // Trigger re-measurement
        setMeasurements((prev) => {
          const updated = [...prev];
          let offset = 0;
          for (let i = 0; i < items.length; i++) {
            const k = getItemKey(items[i], i);
            const h = measurementCacheRef.current.get(k) ?? estimatedItemHeight;
            if (updated[i]) {
              updated[i] = { offset, height: h };
            }
            offset += h;
          }
          return updated;
        });
      }
    },
    [items, getItemKey, estimatedItemHeight]
  );

  if (!shouldVirtualize) {
    // Simple mode for short lists
    return (
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className={`overflow-y-auto ${className}`}
      >
        {items.map((item, index) => (
          <div key={getItemKey(item, index)}>
            {renderItem(item, index)}
          </div>
        ))}
      </div>
    );
  }

  // Virtualized mode
  const visibleItems = items.slice(startIndex, endIndex + 1);
  const offsetTop = measurements[startIndex]?.offset ?? startIndex * estimatedItemHeight;

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className={`overflow-y-auto ${className}`}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetTop}px)` }}>
          {visibleItems.map((item, i) => {
            const actualIndex = startIndex + i;
            const key = getItemKey(item, actualIndex);
            return (
              <div
                key={key}
                ref={(el) => measureRef(el, key)}
              >
                {renderItem(item, actualIndex)}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/**
 * scrollToBottom — Utility for imperative scroll control
 */
export function scrollToBottom(el: HTMLElement | null, behavior: ScrollBehavior = 'smooth') {
  if (el) {
    el.scrollTo({ top: el.scrollHeight, behavior });
  }
}
