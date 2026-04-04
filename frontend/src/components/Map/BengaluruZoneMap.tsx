import { MapContainer, TileLayer, Circle, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect, useState } from 'react'
import type { ZoneSignalData } from '../../types'

interface ZoneMapData {
  id: string
  name: string
  lat: number
  lng: number
  riskScore: number
  riskTier: string
  activeRiders: number
  weeklyPremium: number
  signalStatus?: string
  isSelected?: boolean
}

interface Props {
  zones: ZoneMapData[]
  onZoneClick?: (zoneId: string) => void
  selectedZoneId?: string
  height?: string
  mobileHeight?: string
  showPopups?: boolean
  signalData?: Record<string, ZoneSignalData>
}

const ZONE_COORDS: Record<string, { lat: number; lng: number }> = {
  'hsr': { lat: 12.9116, lng: 77.6389 },
  'koramangala': { lat: 12.9352, lng: 77.6245 },
  'whitefield': { lat: 12.9698, lng: 77.7500 },
  'indiranagar': { lat: 12.9784, lng: 77.6408 },
  'electronic-city': { lat: 12.8399, lng: 77.6770 },
  'bellandur': { lat: 12.9256, lng: 77.6780 },
  'btm-layout': { lat: 12.9166, lng: 77.6101 },
  'jp-nagar': { lat: 12.9063, lng: 77.5857 },
  'yelahanka': { lat: 13.1007, lng: 77.5963 },
  'hebbal': { lat: 13.0358, lng: 77.5970 },
}

function riskColor(score: number, disrupted?: boolean): string {
  if (disrupted) return '#ef4444'
  if (score < 30) return '#10b981'
  if (score < 55) return '#f59e0b'
  if (score < 75) return '#f97316'
  return '#ef4444'
}

function FitBounds({ zones }: { zones: ZoneMapData[] }) {
  const map = useMap()
  useEffect(() => {
    if (zones.length > 0) {
      const bounds = zones.map(z => {
        const coords = ZONE_COORDS[z.id] || { lat: z.lat, lng: z.lng }
        return [coords.lat, coords.lng] as [number, number]
      })
      map.fitBounds(bounds, { padding: [30, 30] })
    }
  }, [zones, map])
  return null
}

export default function BengaluruZoneMap({
  zones,
  onZoneClick,
  selectedZoneId,
  height = '400px',
  mobileHeight,
  showPopups = true,
  signalData,
}: Props) {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 640)
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const effectiveHeight = isMobile && mobileHeight ? mobileHeight : height
  // Ensure minimum height of 200px on mobile
  const minHeight = isMobile ? '200px' : undefined

  return (
    <MapContainer
      center={[12.9716, 77.5946]}
      zoom={11}
      style={{ 
        height: effectiveHeight, 
        minHeight,
        width: '100%', 
        borderRadius: '12px',
        touchAction: 'pan-x pan-y'  // Better touch handling
      }}
      scrollWheelZoom={true}
      zoomControl={true}
      dragging={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://carto.com">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      <FitBounds zones={zones} />

      {zones.map((zone) => {
        const coords = ZONE_COORDS[zone.id] || { lat: zone.lat, lng: zone.lng }
        const isSelected = selectedZoneId === zone.id
        const signal = signalData?.[zone.id]
        const isDisrupted = signal?.is_disrupted

        return (
          <Circle
            key={zone.id}
            center={[coords.lat, coords.lng]}
            radius={isSelected ? 1200 : 900}
            pathOptions={{
              color: riskColor(zone.riskScore, isDisrupted),
              fillColor: riskColor(zone.riskScore, isDisrupted),
              fillOpacity: isSelected ? 0.5 : 0.3,
              weight: isSelected ? 3 : 1.5,
            }}
            eventHandlers={{
              click: () => onZoneClick?.(zone.id),
            }}
          >
            {showPopups && (
              <Popup>
                <div style={{ minWidth: '160px', maxWidth: '220px' }}>
                  <strong style={{ fontSize: '14px', display: 'block', marginBottom: '4px' }}>{zone.name}</strong>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    <div>Risk Score: <b>{zone.riskScore}/100</b></div>
                    <div>Premium: <b>₹{zone.weeklyPremium}/wk</b></div>
                    <div>Active Riders: <b>{zone.activeRiders}</b></div>
                    {isDisrupted && (
                      <div style={{ color: '#ef4444', fontWeight: 'bold', marginTop: '4px', fontSize: '11px' }}>
                        ⚠ DISRUPTION ACTIVE — {signal?.confidence}
                      </div>
                    )}
                  </div>
                </div>
              </Popup>
            )}
          </Circle>
        )
      })}
    </MapContainer>
  )
}
