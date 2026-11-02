import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  api,
  fetchAttachmentBlob,
  formatFileSize,
  uploadAssetAttachments,
  type AssetAttachment,
} from '../api';

interface Props {
  assetId: string;
}

function AttachmentImage({ attachment }: { attachment: AssetAttachment }) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;
    fetchAttachmentBlob(attachment.id)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch(() => setUrl(null));
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [attachment.id]);

  if (!url) {
    return <div className="attachment-thumb attachment-thumb--loading" />;
  }

  return <img src={url} alt={attachment.file_name} className="attachment-thumb" />;
}

export default function AssetAttachments({ assetId }: Props) {
  const qc = useQueryClient();
  const photoInputRef = useRef<HTMLInputElement>(null);
  const docInputRef = useRef<HTMLInputElement>(null);
  const [uploadError, setUploadError] = useState('');

  const { data: attachments, isLoading } = useQuery({
    queryKey: ['asset-attachments', assetId],
    queryFn: () => api<AssetAttachment[]>(`/v1/assets/${assetId}/attachments`),
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ['asset-attachments', assetId] });

  const uploadMutation = useMutation({
    mutationFn: ({ files, kind, setPrimary }: { files: File[]; kind: 'photo' | 'document'; setPrimary?: boolean }) =>
      uploadAssetAttachments(assetId, files, { kind, setPrimary }),
    onSuccess: () => {
      setUploadError('');
      invalidate();
    },
    onError: (err: Error) => setUploadError(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/assets/attachments/${id}`, { method: 'DELETE' }),
    onSuccess: invalidate,
  });

  const primaryMutation = useMutation({
    mutationFn: (id: string) => api(`/v1/assets/attachments/${id}/primary`, { method: 'PUT' }),
    onSuccess: invalidate,
  });

  const photos = (attachments ?? []).filter((a) => a.kind === 'PHOTO');
  const documents = (attachments ?? []).filter((a) => a.kind === 'DOCUMENT');
  const primaryPhoto = photos.find((p) => p.is_primary) ?? photos[0];

  const handleFiles = (fileList: FileList | null, kind: 'photo' | 'document', setPrimary = false) => {
    if (!fileList?.length) return;
    uploadMutation.mutate({ files: Array.from(fileList), kind, setPrimary });
  };

  const downloadFile = async (att: AssetAttachment) => {
    const blob = await fetchAttachmentBlob(att.id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = att.file_name;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return <div className="attachments-panel attachments-panel--loading">Loading attachments…</div>;
  }

  return (
    <div className="attachments-panel">
      <section className="attachment-section">
        <div className="attachment-section-header">
          <div>
            <h4>Asset Photo</h4>
            <p>Primary photo shown in the asset registry. Upload one or more images.</p>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => photoInputRef.current?.click()}
            disabled={uploadMutation.isPending}
          >
            Upload Photos
          </button>
          <input
            ref={photoInputRef}
            type="file"
            accept="image/*"
            multiple
            hidden
            onChange={(e) => handleFiles(e.target.files, 'photo', !primaryPhoto)}
          />
        </div>

        {primaryPhoto ? (
          <div className="primary-photo-wrap">
            <AttachmentImage attachment={primaryPhoto} />
            <div className="primary-photo-meta">
              <strong>{primaryPhoto.file_name}</strong>
              <span>{formatFileSize(primaryPhoto.file_size)}</span>
            </div>
          </div>
        ) : (
          <div
            className="upload-dropzone"
            onClick={() => photoInputRef.current?.click()}
            onKeyDown={(e) => e.key === 'Enter' && photoInputRef.current?.click()}
            role="button"
            tabIndex={0}
          >
            <span>Click to upload asset photos</span>
            <small>JPEG, PNG, WebP — multiple files supported</small>
          </div>
        )}

        {photos.length > 1 && (
          <div className="photo-gallery">
            {photos.map((photo) => (
              <div key={photo.id} className={`photo-card${photo.is_primary ? ' photo-card--primary' : ''}`}>
                <AttachmentImage attachment={photo} />
                <div className="photo-card-actions">
                  {!photo.is_primary && (
                    <button type="button" className="btn btn-ghost btn-sm" onClick={() => primaryMutation.mutate(photo.id)}>
                      Set Primary
                    </button>
                  )}
                  <button type="button" className="btn btn-danger btn-sm" onClick={() => deleteMutation.mutate(photo.id)}>
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {photos.length === 1 && (
          <div className="photo-single-actions">
            <button type="button" className="btn btn-danger btn-sm" onClick={() => deleteMutation.mutate(primaryPhoto!.id)}>
              Remove Photo
            </button>
          </div>
        )}
      </section>

      <section className="attachment-section">
        <div className="attachment-section-header">
          <div>
            <h4>Attachments</h4>
            <p>Manuals, spec sheets, warranties, and other documents.</p>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => docInputRef.current?.click()}
            disabled={uploadMutation.isPending}
          >
            Add Files
          </button>
          <input
            ref={docInputRef}
            type="file"
            multiple
            hidden
            onChange={(e) => handleFiles(e.target.files, 'document')}
          />
        </div>

        {documents.length === 0 ? (
          <div
            className="upload-dropzone upload-dropzone--compact"
            onClick={() => docInputRef.current?.click()}
            onKeyDown={(e) => e.key === 'Enter' && docInputRef.current?.click()}
            role="button"
            tabIndex={0}
          >
            <span>No attachments yet</span>
            <small>Upload manuals, PDFs, spreadsheets, or other files</small>
          </div>
        ) : (
          <ul className="attachment-list">
            {documents.map((doc) => (
              <li key={doc.id} className="attachment-list-item">
                <div className="attachment-list-info">
                  <strong>{doc.file_name}</strong>
                  <span>{formatFileSize(doc.file_size)} · {new Date(doc.created_at).toLocaleDateString()}</span>
                </div>
                <div className="attachment-list-actions">
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => downloadFile(doc)}>
                    Download
                  </button>
                  <button type="button" className="btn btn-danger btn-sm" onClick={() => deleteMutation.mutate(doc.id)}>
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {uploadMutation.isPending && <div className="attachment-upload-status">Uploading…</div>}
      {uploadError && <div className="error">{uploadError}</div>}
    </div>
  );
}
