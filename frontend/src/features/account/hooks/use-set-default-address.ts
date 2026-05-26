import { useMutation, useQueryClient } from "@tanstack/react-query";
import { accountQueryKeys } from "../constants/account-query-keys";
import { addressService } from "../services/address.service";

/**
 * Ustawia domyślny adres użytkownika.
 */
export function useSetDefaultAddress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: addressService.setDefault,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: accountQueryKeys.addresses(),
      });
    },
  });
}
