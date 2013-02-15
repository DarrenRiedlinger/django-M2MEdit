# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DemoModel'
        db.create_table('demoapp_demomodel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sometext', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('attachments', self.gf('upload.models.FileSetField')(to=orm['upload.FileSet'], unique=True, null=True, blank=True)),
        ))
        db.send_create_signal('demoapp', ['DemoModel'])


    def backwards(self, orm):
        # Deleting model 'DemoModel'
        db.delete_table('demoapp_demomodel')


    models = {
        'demoapp.demomodel': {
            'Meta': {'object_name': 'DemoModel'},
            'attachments': ('upload.models.FileSetField', [], {'to': "orm['upload.FileSet']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sometext': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
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

    complete_apps = ['demoapp']