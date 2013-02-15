# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'File'
        db.create_table('upload_file', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('document', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('thumb_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('upload_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('upload', ['File'])

        # Adding model 'FileSet'
        db.create_table('upload_fileset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('upload', ['FileSet'])

        # Adding M2M table for field files on 'FileSet'
        db.create_table('upload_fileset_files', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('fileset', models.ForeignKey(orm['upload.fileset'], null=False)),
            ('file', models.ForeignKey(orm['upload.file'], null=False))
        ))
        db.create_unique('upload_fileset_files', ['fileset_id', 'file_id'])


    def backwards(self, orm):
        # Deleting model 'File'
        db.delete_table('upload_file')

        # Deleting model 'FileSet'
        db.delete_table('upload_fileset')

        # Removing M2M table for field files on 'FileSet'
        db.delete_table('upload_fileset_files')


    models = {
        'upload.file': {
            'Meta': {'object_name': 'File'},
            'document': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'thumb_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'upload_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'upload.fileset': {
            'Meta': {'object_name': 'FileSet'},
            'files': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['upload.File']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['upload']