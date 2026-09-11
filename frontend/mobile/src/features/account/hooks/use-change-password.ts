import { useMutation } from "@tanstack/react-query";
import { securityService } from "../services/security.service";

/**
 * Zmienia hasło aktualnie zalogowanego użytkownika.
 */
export function useChangePassword() {
  return useMutation({
    mutationFn: securityService.changePassword,
  });
}
