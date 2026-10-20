import { useEffect, useRef } from 'react';
export function useNativeDialog(open: boolean) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (open && !dialogRef.current?.open) dialogRef.current?.showModal();
    if (!open) dialogRef.current?.close();
  }, [open]);
  return dialogRef;
}
