# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'File.is_image'
        db.delete_column('upload_file', 'is_image')


    def backwards(self, orm):
        # Adding field 'File.is_image'
        db.add_column('upload_file', 'is_image',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    models = {
        'upload.file': {
            'Meta': {'object_name': 'File'},
            'document': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'upload_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'upload.fileset': {
            'Meta': {'object_name': 'FileSet'},
            'files': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['upload.File']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['upload']