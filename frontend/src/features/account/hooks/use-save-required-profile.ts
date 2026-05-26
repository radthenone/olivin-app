import { useMutation, useQueryClient } from "@tanstack/react-query";
import { accountQueryKeys } from "../constants/account-query-keys";
import { profileService } from "../services/profile.service";

/**
 * Zapisuje minimalne dane profilu wymagane przed wejściem do aplikacji.
 */
export function useSaveRequiredProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: profileService.saveRequiredData,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: accountQueryKeys.currentProfile(),
      });
    },
  });
}
