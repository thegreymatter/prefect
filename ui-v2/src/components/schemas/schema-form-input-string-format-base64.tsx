import { useState, useRef } from "react";
import { Input } from "../ui/input";
import { Button } from "../ui/button/button";
import { cn } from "@/utils";
import { ICONS } from "../ui/icons/constants";

export type SchemaFormInputStringFormatBase64Props = {
	value: string | undefined;
	onValueChange: (value: string | undefined) => void;
	id: string;
	maxSizeBytes?: number; // Default 10MB
	accept?: string; // File types to accept
};

type FileInfo = {
	name: string;
	size: number;
	type: string;
};

const DEFAULT_MAX_SIZE = 10 * 1024 * 1024; // 10MB

const formatFileSize = (bytes: number): string => {
	if (bytes === 0) return "0 Bytes";
	const k = 1024;
	const sizes = ["Bytes", "KB", "MB", "GB"];
	const i = Math.floor(Math.log(bytes) / Math.log(k));
	return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`;
};

export function SchemaFormInputStringFormatBase64({
	value,
	onValueChange,
	id,
	maxSizeBytes = DEFAULT_MAX_SIZE,
	accept,
}: SchemaFormInputStringFormatBase64Props) {
	const [fileInfo, setFileInfo] = useState<FileInfo | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [isLoading, setIsLoading] = useState(false);
	const fileInputRef = useRef<HTMLInputElement>(null);

	const handleFileChange = async (
		event: React.ChangeEvent<HTMLInputElement>,
	) => {
		const file = event.target.files?.[0];
		if (!file) {
			return;
		}

		// Reset error state
		setError(null);

		// Validate file size
		if (file.size > maxSizeBytes) {
			setError(
				`File size (${formatFileSize(file.size)}) exceeds maximum allowed size (${formatFileSize(maxSizeBytes)})`,
			);
			// Clear the input
			if (fileInputRef.current) {
				fileInputRef.current.value = "";
			}
			return;
		}

		setIsLoading(true);

		try {
			// Read file and convert to base64
			const base64String = await fileToBase64(file);

			// Store file info for display
			setFileInfo({
				name: file.name,
				size: file.size,
				type: file.type,
			});

			// Pass the base64 string to the form
			onValueChange(base64String);
		} catch (err) {
			setError(
				`Failed to process file: ${err instanceof Error ? err.message : "Unknown error"}`,
			);
			// Clear the input
			if (fileInputRef.current) {
				fileInputRef.current.value = "";
			}
		} finally {
			setIsLoading(false);
		}
	};

	const fileToBase64 = (file: File): Promise<string> => {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();

			reader.onload = () => {
				try {
					const arrayBuffer = reader.result as ArrayBuffer;
					const bytes = new Uint8Array(arrayBuffer);
					let binary = "";
					for (let i = 0; i < bytes.byteLength; i++) {
						binary += String.fromCharCode(bytes[i]);
					}
					const base64 = btoa(binary);
					resolve(base64);
				} catch (err) {
					reject(err);
				}
			};

			reader.onerror = () => {
				reject(new Error("Failed to read file"));
			};

			reader.readAsArrayBuffer(file);
		});
	};

	const handleClear = () => {
		setFileInfo(null);
		setError(null);
		onValueChange(undefined);
		if (fileInputRef.current) {
			fileInputRef.current.value = "";
		}
	};

	return (
		<div className="space-y-2">
			<div className="flex items-center gap-2">
				<Input
					ref={fileInputRef}
					type="file"
					onChange={handleFileChange}
					id={id}
					accept={accept}
					disabled={isLoading}
					className={cn(
						"cursor-pointer",
						fileInfo && "hidden", // Hide input when file is selected
					)}
				/>
				{fileInfo && (
					<div className="flex items-center gap-2 flex-1 p-2 border border-input rounded-md bg-muted/50">
						<ICONS.File className="size-4 text-muted-foreground flex-shrink-0" />
						<div className="flex-1 min-w-0">
							<p className="text-sm font-medium truncate">{fileInfo.name}</p>
							<p className="text-xs text-muted-foreground">
								{formatFileSize(fileInfo.size)}
								{fileInfo.type && ` • ${fileInfo.type}`}
							</p>
						</div>
						<Button
							type="button"
							variant="ghost"
							size="sm"
							onClick={handleClear}
							disabled={isLoading}
							className="flex-shrink-0"
						>
							<ICONS.X className="size-4" />
						</Button>
					</div>
				)}
			</div>
			{error && (
				<p className="text-sm text-destructive flex items-center gap-1">
					<ICONS.AlertCircle className="size-4" />
					{error}
				</p>
			)}
			{isLoading && (
				<p className="text-sm text-muted-foreground">Processing file...</p>
			)}
			<p className="text-xs text-muted-foreground">
				Max file size: {formatFileSize(maxSizeBytes)}
			</p>
		</div>
	);
}
