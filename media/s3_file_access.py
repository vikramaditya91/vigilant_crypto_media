import os
import boto3
import tempfile


class S3FileAccessAbstract:
    def __init__(self,
                 bucket_name="vikramaditya91.github.io",
                 push_back=False,
                 file_name=None,
                 file_exists=True):
        self.s3 = boto3.resource("s3")
        self.bucket = bucket_name
        self.push_back = push_back
        self.file_name = file_name
        self.file_exists = file_exists

    def __enter__(self):
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as fp:
            self.tempfile_name = fp.name
            if self.file_exists:
                self.s3.Bucket(self.bucket).download_file(self.file_name, fp.name)
            return fp.name

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.push_back:
            self.s3.Bucket(self.bucket).upload_file(self.tempfile_name, self.file_name)
        os.remove(self.tempfile_name)

    def list_files(self, prefix_add=None):
        all_objects = boto3.client('s3').list_objects(Bucket=self.bucket, Prefix=f"{self.file_name}{prefix_add}")
        if "Contents" not in all_objects:
            return []
        return all_objects['Contents']


class DBFileAccess(S3FileAccessAbstract):
    def __init__(self,
                 *args, **kwargs):
        super(DBFileAccess, self).__init__(*args, **kwargs)
        self.file_name = "db/coin_prediction.db"
