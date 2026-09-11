import { useMutation, useQueryClient } from "@tanstack/react-query";
import { accountQueryKeys } from "../constants/account-query-keys";
import { profileService } from "../services/profile.service";

/**
 * Zapisuje edytowalne dane profilu aktualnego użytkownika.
 */
export function useSaveProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: profileService.saveEditableData,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: accountQueryKeys.currentProfile(),
      });
    },
  });
}
