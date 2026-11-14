from packages.provenance.sources import digest


class S3Artifacts:
    """Adapter for versioned buckets that enforce write-once objects."""
    def __init__(self, client, bucket: str):
        self.client, self.bucket = client, bucket

    def put(self, data: bytes) -> str:
        key = digest(data)
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=data, IfNoneMatch='*')
        except self.client.exceptions.ClientError as exc:
            if exc.response['ResponseMetadata']['HTTPStatusCode'] != 412:
                raise
        self.get(key)
        return key

    def get(self, checksum: str) -> bytes:
        if len(checksum) != 64 or any(c not in '0123456789abcdef' for c in checksum):
            raise ValueError('Invalid artifact digest')
        response = self.client.get_object(Bucket=self.bucket, Key=checksum)
        with response['Body'] as stream:
            data = stream.read()
        if digest(data) != checksum:
            raise OSError('Artifact checksum mismatch')
        return data
