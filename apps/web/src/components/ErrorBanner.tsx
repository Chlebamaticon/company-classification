interface Props {
  message: string;
  onDismiss: () => void;
}

export default function ErrorBanner({ message, onDismiss }: Props) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-4">
      <div className="flex items-start justify-between">
        <div className="flex gap-2">
          <span className="text-red-500">⚠</span>
          <p className="text-sm text-red-700">{message}</p>
        </div>
        <button
          type="button"
          onClick={onDismiss}
          className="text-sm font-medium text-red-600 hover:underline"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
