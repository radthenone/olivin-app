import { View } from "react-native";
import type { LayoutProps } from "./PageLayout.types";

const PageLayout = ({ children }: LayoutProps) => {
  return <View>{children}</View>;
};

export default PageLayout;
