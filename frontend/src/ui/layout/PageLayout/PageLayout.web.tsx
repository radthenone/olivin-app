import type { WebLayoutProps, LayoutProps } from "./PageLayout.types";
import { LAYOUT_CONSTANTS } from "./PageLayout.constants";
import { generateGridStyles } from "./PageLayout.utils";

const PageLayoutWeb = ({
  children,
  className,
  layout = LAYOUT_CONSTANTS,
}: WebLayoutProps) => {
  const { gridTemplateColumns, gridTemplateRows, gridTemplateAreas } =
    generateGridStyles(layout);

  return (
    <div
      className={
        className
          ? `grid min-h-screen ${gridTemplateColumns} ${gridTemplateRows} ${gridTemplateAreas}
      ${className}`
          : `grid min-h-screen ${gridTemplateColumns} ${gridTemplateRows} ${gridTemplateAreas}`
      }
    >
      {children}
    </div>
  );
};

export default PageLayoutWeb;
