/**
 * Asset Management - Track company assets and maintenance
 */
import React, { useState, useEffect } from 'react';
import { assetsApi, Asset, MaintenanceLog } from '../api/assets';
import { LoadingSpinner } from '../components/LoadingSpinner';
import './AssetManagement.css';

export const AssetManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'assets' | 'maintenance'>('assets');
  const [assets, setAssets] = useState<Asset[]>([]);
  const [maintenanceLogs, setMaintenanceLogs] = useState<MaintenanceLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAssetModal, setShowAssetModal] = useState(false);
  const [showMaintenanceModal, setShowMaintenanceModal] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterCategory, setFilterCategory] = useState<string>('');

  const [assetForm, setAssetForm] = useState({
    asset_tag: '',
    name: '',
    description: '',
    category: 'computer',
    status: 'active',
    purchase_price: '',
    purchase_date: '',
    useful_life_years: 3,
    location: '',
    manufacturer: '',
    model_number: '',
    serial_number: ''
  });

  const [maintenanceForm, setMaintenanceForm] = useState({
    asset: 0,
    maintenance_type: 'preventive',
    status: 'scheduled',
    description: '',
    scheduled_date: '',
    performed_by: '',
    vendor: '',
    cost: '0.00'
  });

  useEffect(() => {
    loadData();
  }, [filterStatus, filterCategory]);

  const loadData = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (filterStatus) params.status = filterStatus;
      if (filterCategory) params.category = filterCategory;

      const [assetsRes, maintenanceRes] = await Promise.all([
        assetsApi.listAssets(params),
        assetsApi.listMaintenanceLogs()
      ]);

      setAssets(assetsRes.data.results || []);
      setMaintenanceLogs(maintenanceRes.data.results || []);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAsset = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await assetsApi.createAsset(assetForm);
      setShowAssetModal(false);
      resetAssetForm();
      loadData();
    } catch (error) {
      console.error('Error creating asset:', error);
      alert('Failed to create asset');
    }
  };

  const handleCreateMaintenance = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await assetsApi.createMaintenanceLog(maintenanceForm);
      setShowMaintenanceModal(false);
      resetMaintenanceForm();
      loadData();
    } catch (error) {
      console.error('Error creating maintenance log:', error);
      alert('Failed to create maintenance log');
    }
  };

  const handleUpdateAssetStatus = async (asset: Asset, newStatus: string) => {
    try {
      await assetsApi.updateAsset(asset.id, { status: newStatus });
      loadData();
    } catch (error) {
      console.error('Error updating asset:', error);
      alert('Failed to update asset status');
    }
  };

  const resetAssetForm = () => {
    setAssetForm({
      asset_tag: '',
      name: '',
      description: '',
      category: 'computer',
      status: 'active',
      purchase_price: '',
      purchase_date: '',
      useful_life_years: 3,
      location: '',
      manufacturer: '',
      model_number: '',
      serial_number: ''
    });
  };

  const resetMaintenanceForm = () => {
    setMaintenanceForm({
      asset: 0,
      maintenance_type: 'preventive',
      status: 'scheduled',
      description: '',
      scheduled_date: '',
      performed_by: '',
      vendor: '',
      cost: '0.00'
    });
  };

  const getCategoryIcon = (category: string): string => {
    const icons: { [key: string]: string } = {
      computer: '💻',
      software: '💿',
      furniture: '🪑',
      vehicle: '🚗',
      other: '📦'
    };
    return icons[category] || '📦';
  };

  const getStatusColor = (status: string): string => {
    const colors: { [key: string]: string } = {
      active: 'status-active',
      in_repair: 'status-repair',
      retired: 'status-retired',
      lost: 'status-lost',
      disposed: 'status-disposed'
    };
    return colors[status] || '';
  };

  if (loading) {
    return <LoadingSpinner message="Loading assets..." />;
  }

  return (
    <div className="asset-management">
      <header className="asset-header">
        <div>
          <h1>Asset Management</h1>
          <p>Track company equipment, software, and resources</p>
        </div>
        <button className="btn-primary" onClick={() => setShowAssetModal(true)}>
          + Add Asset
        </button>
      </header>

      {/* Stats Summary */}
      <div className="asset-stats">
        <div className="stat-box">
          <h3>{assets.filter(a => a.status === 'active').length}</h3>
          <p>Active Assets</p>
        </div>
        <div className="stat-box">
          <h3>{assets.filter(a => a.status === 'in_repair').length}</h3>
          <p>In Repair</p>
        </div>
        <div className="stat-box">
          <h3>{maintenanceLogs.filter(m => m.status === 'scheduled').length}</h3>
          <p>Scheduled Maintenance</p>
        </div>
        <div className="stat-box">
          <h3>${assets.reduce((sum, a) => sum + parseFloat(a.purchase_price || '0'), 0).toLocaleString()}</h3>
          <p>Total Value</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="asset-tabs">
        <button
          className={`tab ${activeTab === 'assets' ? 'active' : ''}`}
          onClick={() => setActiveTab('assets')}
        >
          Assets ({assets.length})
        </button>
        <button
          className={`tab ${activeTab === 'maintenance' ? 'active' : ''}`}
          onClick={() => setActiveTab('maintenance')}
        >
          Maintenance ({maintenanceLogs.length})
        </button>
      </div>

      {/* Filters */}
      {activeTab === 'assets' && (
        <div className="asset-filters">
          <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
            <option value="">All Categories</option>
            <option value="computer">Computer Equipment</option>
            <option value="software">Software License</option>
            <option value="furniture">Furniture</option>
            <option value="vehicle">Vehicle</option>
            <option value="other">Other</option>
          </select>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="in_repair">In Repair</option>
            <option value="retired">Retired</option>
            <option value="lost">Lost/Stolen</option>
            <option value="disposed">Disposed</option>
          </select>
        </div>
      )}

      {/* Content */}
      {activeTab === 'assets' ? (
        <div className="assets-grid">
          {assets.map((asset) => (
            <div key={asset.id} className="asset-card">
              <div className="asset-card-header">
                <div className="asset-icon">{getCategoryIcon(asset.category)}</div>
                <div className="asset-title">
                  <h3>{asset.name}</h3>
                  <span className="asset-tag">{asset.asset_tag}</span>
                </div>
                <span className={`asset-status ${getStatusColor(asset.status)}`}>
                  {asset.status.replace('_', ' ')}
                </span>
              </div>
              <div className="asset-card-body">
                <div className="asset-detail">
                  <strong>Assigned To:</strong> {asset.assigned_to_name || 'Unassigned'}
                </div>
                <div className="asset-detail">
                  <strong>Location:</strong> {asset.location || 'N/A'}
                </div>
                <div className="asset-detail">
                  <strong>Purchase Price:</strong> ${parseFloat(asset.purchase_price).toLocaleString()}
                </div>
                <div className="asset-detail">
                  <strong>Purchase Date:</strong> {new Date(asset.purchase_date).toLocaleDateString()}
                </div>
                {asset.manufacturer && (
                  <div className="asset-detail">
                    <strong>Manufacturer:</strong> {asset.manufacturer} {asset.model_number}
                  </div>
                )}
              </div>
              <div className="asset-card-actions">
                <button
                  className="btn-small btn-schedule"
                  onClick={() => {
                    setMaintenanceForm({ ...maintenanceForm, asset: asset.id });
                    setShowMaintenanceModal(true);
                  }}
                >
                  Schedule Maintenance
                </button>
                <select
                  value={asset.status}
                  onChange={(e) => handleUpdateAssetStatus(asset, e.target.value)}
                  className="status-select"
                >
                  <option value="active">Active</option>
                  <option value="in_repair">In Repair</option>
                  <option value="retired">Retired</option>
                  <option value="lost">Lost/Stolen</option>
                  <option value="disposed">Disposed</option>
                </select>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="maintenance-list">
          <div className="maintenance-header">
            <h2>Maintenance Schedule</h2>
            <button className="btn-primary" onClick={() => setShowMaintenanceModal(true)}>
              + Schedule Maintenance
            </button>
          </div>
          <table className="maintenance-table">
            <thead>
              <tr>
                <th>Asset</th>
                <th>Type</th>
                <th>Description</th>
                <th>Scheduled Date</th>
                <th>Performed By</th>
                <th>Cost</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {maintenanceLogs.map((log) => (
                <tr key={log.id}>
                  <td>
                    <strong>{log.asset_name}</strong>
                    <br />
                    <small>{log.asset_tag}</small>
                  </td>
                  <td>{log.maintenance_type}</td>
                  <td>{log.description}</td>
                  <td>{new Date(log.scheduled_date).toLocaleDateString()}</td>
                  <td>{log.performed_by}</td>
                  <td>${parseFloat(log.cost).toLocaleString()}</td>
                  <td>
                    <span className={`maintenance-status status-${log.status}`}>
                      {log.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Asset Modal */}
      {showAssetModal && (
        <div className="modal-overlay" onClick={() => setShowAssetModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Add New Asset</h2>
            <form onSubmit={handleCreateAsset}>
              <div className="form-row">
                <div className="form-group">
                  <label>Asset Tag *</label>
                  <input
                    type="text"
                    value={assetForm.asset_tag}
                    onChange={(e) => setAssetForm({ ...assetForm, asset_tag: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Name *</label>
                  <input
                    type="text"
                    value={assetForm.name}
                    onChange={(e) => setAssetForm({ ...assetForm, name: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={assetForm.description}
                  onChange={(e) => setAssetForm({ ...assetForm, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Category *</label>
                  <select
                    value={assetForm.category}
                    onChange={(e) => setAssetForm({ ...assetForm, category: e.target.value })}
                  >
                    <option value="computer">Computer Equipment</option>
                    <option value="software">Software License</option>
                    <option value="furniture">Furniture</option>
                    <option value="vehicle">Vehicle</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Status *</label>
                  <select
                    value={assetForm.status}
                    onChange={(e) => setAssetForm({ ...assetForm, status: e.target.value })}
                  >
                    <option value="active">Active</option>
                    <option value="in_repair">In Repair</option>
                    <option value="retired">Retired</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Purchase Price *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={assetForm.purchase_price}
                    onChange={(e) => setAssetForm({ ...assetForm, purchase_price: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Purchase Date *</label>
                  <input
                    type="date"
                    value={assetForm.purchase_date}
                    onChange={(e) => setAssetForm({ ...assetForm, purchase_date: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Location</label>
                  <input
                    type="text"
                    value={assetForm.location}
                    onChange={(e) => setAssetForm({ ...assetForm, location: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Manufacturer</label>
                  <input
                    type="text"
                    value={assetForm.manufacturer}
                    onChange={(e) => setAssetForm({ ...assetForm, manufacturer: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-actions">
                <button type="button" onClick={() => setShowAssetModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create Asset
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Schedule Maintenance Modal */}
      {showMaintenanceModal && (
        <div className="modal-overlay" onClick={() => setShowMaintenanceModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Schedule Maintenance</h2>
            <form onSubmit={handleCreateMaintenance}>
              <div className="form-group">
                <label>Asset *</label>
                <select
                  value={maintenanceForm.asset}
                  onChange={(e) => setMaintenanceForm({ ...maintenanceForm, asset: parseInt(e.target.value) })}
                  required
                >
                  <option value={0}>Select Asset</option>
                  {assets.map((asset) => (
                    <option key={asset.id} value={asset.id}>
                      {asset.asset_tag} - {asset.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Maintenance Type *</label>
                  <select
                    value={maintenanceForm.maintenance_type}
                    onChange={(e) => setMaintenanceForm({ ...maintenanceForm, maintenance_type: e.target.value })}
                  >
                    <option value="repair">Repair</option>
                    <option value="preventive">Preventive Maintenance</option>
                    <option value="upgrade">Upgrade</option>
                    <option value="inspection">Inspection</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Status *</label>
                  <select
                    value={maintenanceForm.status}
                    onChange={(e) => setMaintenanceForm({ ...maintenanceForm, status: e.target.value })}
                  >
                    <option value="scheduled">Scheduled</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Description *</label>
                <textarea
                  value={maintenanceForm.description}
                  onChange={(e) => setMaintenanceForm({ ...maintenanceForm, description: e.target.value })}
                  rows={3}
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Scheduled Date *</label>
                  <input
                    type="date"
                    value={maintenanceForm.scheduled_date}
                    onChange={(e) => setMaintenanceForm({ ...maintenanceForm, scheduled_date: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Cost</label>
                  <input
                    type="number"
                    step="0.01"
                    value={maintenanceForm.cost}
                    onChange={(e) => setMaintenanceForm({ ...maintenanceForm, cost: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Performed By *</label>
                  <input
                    type="text"
                    value={maintenanceForm.performed_by}
                    onChange={(e) => setMaintenanceForm({ ...maintenanceForm, performed_by: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Vendor</label>
                  <input
                    type="text"
                    value={maintenanceForm.vendor}
                    onChange={(e) => setMaintenanceForm({ ...maintenanceForm, vendor: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-actions">
                <button type="button" onClick={() => setShowMaintenanceModal(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
