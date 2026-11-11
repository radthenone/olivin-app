import { View } from "react-native";

export function ProductListSkeleton({ count = 4 }: { count?: number }) {
  const items = Array.from({ length: count });

  return (
    <View className="flex-row flex-wrap gap-4 p-4">
      {items.map((_, index) => (
        <View
          key={index}
          className="w-[47%] rounded-xl border border-neutral-200 bg-white p-3"
        >
          <View className="aspect-square w-full rounded-lg bg-neutral-100" />
          <View className="mt-3 gap-2">
            <View className="h-4 w-3/4 rounded-sm bg-neutral-100" />
            <View className="h-4 w-1/2 rounded-sm bg-neutral-100" />
          </View>
        </View>
      ))}
    </View>
  );
}
