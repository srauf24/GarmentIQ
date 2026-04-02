import { useMutation, useQueryClient } from "@tanstack/react-query";

import { uploadImage } from "../api/client";
import type { ImageResponse } from "../types";

interface UploadVariables {
  file: File;
  uploadedBy?: string;
}

export function useUploadImage() {
  const queryClient = useQueryClient();

  return useMutation<ImageResponse, Error, UploadVariables>({
    mutationFn: ({ file, uploadedBy }) => uploadImage(file, uploadedBy),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["images"] });
    },
  });
}
