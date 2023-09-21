--
-- PostgreSQL database dump
--

-- Dumped from database version 14.7 (Ubuntu 14.7-0ubuntu0.22.10.1)
-- Dumped by pg_dump version 14.7 (Ubuntu 14.7-0ubuntu0.22.10.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ways_line; Type: TABLE; Schema: public; Owner: rob
--

CREATE TABLE public.ways_line (
    osm_id bigint NOT NULL,
    uid integer,
    "user" text,
    version integer,
    changeset integer,
    "timestamp" timestamp without time zone,
    tags jsonb,
    geom public.geometry(LineString,4326),
    grid integer
);


ALTER TABLE public.ways_line OWNER TO rob;

--
-- Name: ways_line_geom_idx; Type: INDEX; Schema: public; Owner: rob
--

CREATE INDEX ways_line_geom_idx ON public.ways_line USING gist (geom) WITH (fillfactor='100');


--
-- PostgreSQL database dump complete
--

