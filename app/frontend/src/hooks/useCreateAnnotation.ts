import { useMutation, useQueryClient } from "@tanstack/react-query";

import { createAnnotation } from "../api/client";
import type { AnnotationCreate, AnnotationResponse } from "../types";

interface CreateAnnotationVariables {
  imageId: string;
  body: AnnotationCreate;
}

export function useCreateAnnotation() {
  const queryClient = useQueryClient();

  return useMutation<AnnotationResponse, Error, CreateAnnotationVariables>({
    mutationFn: ({ imageId, body }) => createAnnotation(imageId, body),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["images", variables.imageId] });
      queryClient.invalidateQueries({ queryKey: ["images"] });
    },
  });
}
