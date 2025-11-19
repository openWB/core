import {
  watch,
  onMounted,
  onBeforeUnmount,
  Ref,
  ComputedRef,
  nextTick,
} from 'vue';

export function useEnergyFlowTransition(
  lineElementId: string,
  isActive: Ref<boolean> | ComputedRef<boolean>,
  durationRef: Ref<number> | ComputedRef<number>,
  reverseRef: Ref<boolean> | ComputedRef<boolean>,
) {
  let lineElement: SVGPathElement | null = null;
  let running = false;
  let currentOffset = 0;
  let animationFrameId: number | null = null;

  const handleTransitionEnd = () => {
    if (!running) return;
    animationFrameId = window.requestAnimationFrame(advanceAnimationStep);
  };

  const initializeLineElement = () => {
    lineElement = document.querySelector(
      `#flow-path-${lineElementId}`,
    ) as SVGPathElement | null;
    if (!lineElement) return;
    // Initial setup for dashed line
    lineElement.style.strokeDasharray = '5';
    lineElement.style.transition = 'none';
    lineElement.style.strokeDashoffset = '0';
    currentOffset = 0;
    //css fires a transitionend event when the animation completes
    lineElement.removeEventListener('transitionend', handleTransitionEnd);
    lineElement.addEventListener('transitionend', handleTransitionEnd);
  };

  const syncCurrentOffsetFromDom = () => {
    if (!lineElement) return;
    const strokeDashoffsetString = getComputedStyle(lineElement).strokeDashoffset;
    const strokeDashoffsetValue = parseFloat(strokeDashoffsetString || '0');
    if (!Number.isNaN(strokeDashoffsetValue)) {
      currentOffset = strokeDashoffsetValue;
    }
  };

  const advanceAnimationStep = () => {
    if (!running) return;
    if (!lineElement) {
      initializeLineElement();
      if (!lineElement) return;
    }
    // Before computing next step, read the real offset from DOM
    syncCurrentOffsetFromDom();
    const direction = reverseRef.value ? 1 : -1;
    const duration = durationRef.value || 1;
    const stepSize = 10; // how far one "dash" travels per step
    // New target position in the stroke dash pattern
    const targetOffset = currentOffset + stepSize * direction;
    // Force layout, otherwise browser may optimize away the transition
    lineElement.getBoundingClientRect();
    // Apply new offset with transition
    lineElement.style.transition = `stroke-dashoffset ${duration}s linear`;
    // Animate toward the next position
    lineElement.style.strokeDashoffset = String(targetOffset);
  };

  const start = () => {
    if (running) return;
    running = true;
    if (!lineElement) {
      initializeLineElement();
    }
    if (!lineElement) return;
    animationFrameId = window.requestAnimationFrame(advanceAnimationStep);
  };

  const stop = () => {
    running = false;
    if (animationFrameId !== null) {
      window.cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
    if (lineElement) {
      // Reset strokeDasharray to solid line
      lineElement.style.transition = 'none';
      lineElement.style.strokeDasharray = 'none';
      lineElement.style.strokeDashoffset = '0';
    }
  };

  onMounted(() => {
    if (isActive.value) {
      nextTick().then(() => {
        initializeLineElement();
        if (isActive.value) {
          start();
        }
      });
    }
  });

  onBeforeUnmount(() => {
    stop();
    if (lineElement) {
      lineElement.removeEventListener('transitionend', handleTransitionEnd);
    }
  });

  // Turn animation on/off when this line becomes active/inactive
  watch(
    isActive,
    (active) => {
      if (active) {
        nextTick().then(() => {
          initializeLineElement();
          if (isActive.value) {
            start();
          }
        });
      } else {
        stop();
      }
    },
    { flush: 'post' },
  );

  // When duration or direction changes re-step from the current position
  watch(
    [durationRef, reverseRef],
    () => {
      if (!running || !lineElement) return;
      if (animationFrameId !== null) {
        window.cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
      }
      animationFrameId = window.requestAnimationFrame(advanceAnimationStep);
    },
    { flush: 'post' },
  );
}
