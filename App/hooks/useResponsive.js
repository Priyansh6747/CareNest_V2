import { Platform, useWindowDimensions } from 'react-native';

export const BREAKPOINTS = {
    mobile: 0,
    tablet: 640,
    desktop: 1024,
    wide: 1280,
};

/**
 * Responsive helper shared by every screen.
 *
 * Returns the current window dimensions plus flags and layout helpers so
 * screens stay readable on phones, tablets and desktop browsers.
 */
export default function useResponsive() {
    const { width, height } = useWindowDimensions();

    const isWeb = Platform.OS === 'web';
    const isMobile = width < BREAKPOINTS.tablet;
    const isTablet = width >= BREAKPOINTS.tablet && width < BREAKPOINTS.desktop;
    const isDesktop = width >= BREAKPOINTS.desktop;

    // Web gets a centered column so content does not stretch full width.
    const maxContentWidth = isDesktop ? 1040 : isTablet ? 720 : undefined;

    // Column count for tappable grids.
    const gridColumns = isDesktop ? 4 : isTablet ? 3 : 2;

    return {
        width,
        height,
        isWeb,
        isMobile,
        isTablet,
        isDesktop,
        maxContentWidth,
        gridColumns,
        // Percentage width for a grid cell, accounting for gap gutters.
        gridItemWidth: `${100 / gridColumns}%`,
        // Horizontal page padding scaled to viewport.
        pagePadding: isDesktop ? 32 : isTablet ? 24 : 16,
        // Modal/sheet cards use a comfortable reading measure on large screens.
        cardMaxWidth: isDesktop ? 640 : undefined,
    };
}
