import json
import os
from flask import Blueprint, render_template, request, redirect, url_for, g, flash, current_app
from ..middleware import school_scoped, role_minimum
from ..models import db, PluginState

plugin_admin_bp = Blueprint('plugin_admin', __name__, url_prefix='/admin/plugins',
                             template_folder='templates/plugins')


@plugin_admin_bp.route('/')
@school_scoped
@role_minimum('admin')
def index():
    plugin_manager = current_app.extensions.get('plugin_manager')
    if not plugin_manager:
        flash('Plugin system not initialized.', 'danger')
        return render_template('plugin_admin.html', plugins=[], active_slugs=set())

    plugins = plugin_manager.get_installed_plugins()
    active_slugs = plugin_manager.get_active_slugs()

    plugin_list = []
    for p in plugins:
        record = PluginState.query.filter_by(slug=p['slug']).first()
        plugin_list.append({
            'slug': p['slug'],
            'name': p.get('name', p['slug']),
            'version': p.get('version', '0.0.0'),
            'description': p.get('description', ''),
            'author': p.get('author', ''),
            'is_active': record.is_active if record else False,
            'is_installed': record is not None,
        })

    return render_template('plugin_admin.html', plugins=plugin_list)


@plugin_admin_bp.route('/install/<slug>', methods=['POST'])
@school_scoped
@role_minimum('admin')
def install(slug):
    plugin_manager = current_app.extensions.get('plugin_manager')
    if not plugin_manager or slug not in plugin_manager.plugins:
        flash(f'Plugin "{slug}" not found.', 'danger')
        return redirect(url_for('plugin_admin.index'))

    existing = PluginState.query.filter_by(slug=slug).first()
    if existing:
        existing.is_active = True
        existing.version = plugin_manager.plugins[slug].get('version', '0.0.0')
    else:
        record = PluginState(
            slug=slug,
            is_active=True,
            version=plugin_manager.plugins[slug].get('version', '0.0.0'),
        )
        db.session.add(record)
    db.session.commit()
    flash(f'Plugin "{slug}" installed and enabled.', 'success')
    return redirect(url_for('plugin_admin.index'))


@plugin_admin_bp.route('/toggle/<slug>', methods=['POST'])
@school_scoped
@role_minimum('admin')
def toggle(slug):
    record = PluginState.query.filter_by(slug=slug).first()
    if not record:
        flash(f'Plugin "{slug}" not installed.', 'danger')
        return redirect(url_for('plugin_admin.index'))

    record.is_active = not record.is_active
    db.session.commit()
    status = 'enabled' if record.is_active else 'disabled'
    flash(f'Plugin "{slug}" {status}.', 'success')
    return redirect(url_for('plugin_admin.index'))


@plugin_admin_bp.route('/uninstall/<slug>', methods=['POST'])
@school_scoped
@role_minimum('admin')
def uninstall(slug):
    record = PluginState.query.filter_by(slug=slug).first()
    if record:
        db.session.delete(record)
        db.session.commit()
    flash(f'Plugin "{slug}" uninstalled.', 'info')
    return redirect(url_for('plugin_admin.index'))
