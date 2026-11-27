import toast from 'react-hot-toast';

export const showSuccess = (message: string): string => toast.success(message);
export const showError = (message: string): string => toast.error(message);
export const showLoading = (message: string): string => toast.loading(message);
export const dismissToast = (id?: string): void => toast.dismiss(id);
