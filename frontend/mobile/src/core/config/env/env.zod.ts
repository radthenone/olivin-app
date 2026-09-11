import { z } from "zod";

export const ExtraSchema = z.object({
  webUrl: z.string().min(1),
  androidUrl: z.string().min(1).optional(),
  isDev: z.boolean().default(false),
  appVersion: z.string().default("v1"),
  httpTimeout: z.number().default(30000),
  sessionTokenKey: z.string().default("auth.sessionToken"),
  googleClientId: z.string().optional(),
  googleWebClientId: z.string().optional(),
  googleAndroidClientId: z.string().optional(),
  facebookClientId: z.string().optional(),
});
