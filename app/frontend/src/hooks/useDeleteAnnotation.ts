import { useMutation, useQueryClient } from "@tanstack/react-query";

import { deleteAnnotation } from "../api/client";

interface DeleteAnnotationVariables {
  imageId: string;
  annotationId: string;
}

export function useDeleteAnnotation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, DeleteAnnotationVariables>({
    mutationFn: ({ imageId, annotationId }) =>
      deleteAnnotation(imageId, annotationId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["images", variables.imageId] });
      queryClient.invalidateQueries({ queryKey: ["images"] });
    },
  });
}
